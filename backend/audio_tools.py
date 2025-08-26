# audio_tools.py
# All audio endpoints + credit deduction + 4:30 cap + prompt length caps

import os, math, random, tempfile, subprocess
try:
    import numpy as np, librosa, soundfile as sf
except Exception:
    np = None

# Import Block C limits
try:
    from block_c_limits import (
        MAX_SONG_LENGTH_SECONDS,
        MAX_LYRICS_CHARS,
        MAX_BEAT_DESC_CHARS,
    )
except Exception:
    # Safe fallback if Block C file isn't present
    MAX_SONG_LENGTH_SECONDS = 270
    MAX_LYRICS_CHARS = 3500
    MAX_BEAT_DESC_CHARS = 3500

def register_audio_routes(app, db, Song, current_user, is_max_allowed, _save_new_song):
    from flask import request

    # Lazy-load optional deps here to avoid startup issues
    try:
        from demucs.separate import main as demucs_separate
        DEMUCS_OK = True
    except Exception:
        DEMUCS_OK = False

    try:
        import parselmouth
        from parselmouth.praat import call as praat_call
        PARSELMOUTH_OK = True
    except Exception:
        PARSELMOUTH_OK = False

    try:
        from audiocraft.models import MusicGen
        MUSICGEN = MusicGen.get_pretrained('facebook/musicgen-small')
        MUSICGEN.set_generation_params(duration=20)
    except Exception:
        MUSICGEN = None

    CREDIT_COST = 1  # 1 credit per new output

    def ensure_np():
        if not (np and librosa): return 'Audio libs missing (numpy/librosa).', 500

    def song_cap(y, sr):
        max_len = int(MAX_SONG_LENGTH_SECONDS * sr)
        return y[:max_len]

    def prompt_ok(text):
        return (text is None) or (len(text) <= MAX_BEAT_DESC_CHARS)

    def deduct_credit_or_block():
        """Deduct 1 credit from current user; block if not enough."""
        u = current_user()
        if not u: return 'Not logged in', 401
        if not is_max_allowed(u): return 'Max plan or trial required', 403
        if (u.artistic_time or 0) < CREDIT_COST:
            return 'Insufficient Trainer Time credits', 402
        u.artistic_time -= CREDIT_COST
        db.session.commit()
        return None

    def _song_path(song_id:int):
        s = db.session.get(Song, song_id)
        if not s or not os.path.exists(s.file_path): return None, None
        return s, s.file_path

    # --------- Trim (FREE) ----------
    @app.post('/api/song/trim/<int:song_id>')
    def api_trim(song_id):
        chk = ensure_np()
        if chk: return chk
        u = current_user()
        s, path = _song_path(song_id)
        if not s or s.user_id != u.id: return 'Not found', 404
        start = float(request.form.get('start','0') or 0)
        end = float(request.form.get('end','0') or 0)
        y, sr = librosa.load(path, sr=None, mono=True)
        if end <= 0 or end > len(y)/sr: end = len(y)/sr
        a = max(0, int(start*sr)); b = max(a+1, int(end*sr))
        y2 = y[a:b]
        y2 = song_cap(y2, sr)
        new = _save_new_song(u.id, f'Trim_{s.id}', y2, sr, s.tags)
        return f'✅ Trimmed → {new.title}'

    # --------- Extend (1 credit) ----------
    @app.post('/api/song/extend/<int:song_id>')
    def api_extend(song_id):
        chk = ensure_np()
        if chk: return chk
        fail = deduct_credit_or_block()
        if fail: return fail
        s, path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404
        if not MUSICGEN: return 'MusicGen not available', 501

        seconds_add = max(5, int(request.form.get('seconds','10')))
        tags = (request.form.get('tags') or s.tags or 'atmospheric').strip()
        if not prompt_ok(tags): return f'Prompt too long (max {MAX_BEAT_DESC_CHARS} chars)', 400

        gen = MUSICGEN.generate([f'extend: {tags}'])
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            MUSICGEN.save_wav(gen[0], tmp.name)
            y_add, sr_add = librosa.load(tmp.name, sr=None, mono=True)

        y, sr = librosa.load(path, sr=None, mono=True)
        if sr_add != sr: y_add = librosa.resample(y_add, orig_sr=sr_add, target_sr=sr)
        if len(y_add)/sr > seconds_add: y_add = y_add[:int(seconds_add*sr)]
        y_out = np.concatenate([y, y_add])
        y_out = song_cap(y_out, sr)

        new = _save_new_song(s.user_id, f'Extend_{s.id}', y_out, sr, s.tags)
        return f'✅ Extended → {new.title}'

    # --------- Replace segment (1 credit) ----------
    @app.post('/api/song/replace/<int:song_id>')
    def api_replace(song_id):
        chk = ensure_np()
        if chk: return chk
        fail = deduct_credit_or_block()
        if fail: return fail
        s, path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404
        if not MUSICGEN: return 'MusicGen not available', 501

        start = float(request.form.get('start','0')); end = float(request.form.get('end','0'))
        tags = (request.form.get('tags') or 'remix').strip()
        if not prompt_ok(tags): return f'Prompt too long (max {MAX_BEAT_DESC_CHARS} chars)', 400

        y, sr = librosa.load(path, sr=None, mono=True)
        a = max(0, int(start*sr)); b = max(a+1, int(end*sr)) if end>0 else len(y)
        seg_len = b - a

        gen = MUSICGEN.generate([f'segment: {tags}'])
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            MUSICGEN.save_wav(gen[0], tmp.name)
            y_new, sr_new = librosa.load(tmp.name, sr=None, mono=True)
        if sr_new != sr: y_new = librosa.resample(y_new, orig_sr=sr_new, target_sr=sr)
        if len(y_new) > seg_len: y_new = y_new[:seg_len]
        else: y_new = librosa.util.fix_length(y_new, seg_len)

        y_out = np.concatenate([y[:a], y_new, y[b:]])
        y_out = song_cap(y_out, sr)

        new = _save_new_song(s.user_id, f'Replace_{s.id}', y_out, sr, s.tags)
        return f'✅ Replaced → {new.title}'

    # --------- Remix from prompt (1 credit) ----------
    @app.post('/api/song/remix/<int:song_id>')
    def api_remix(song_id):
        chk = ensure_np()
        if chk: return chk
        fail = deduct_credit_or_block()
        if fail: return fail
        s, path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404
        if not MUSICGEN: return 'MusicGen not available', 501

        tags = (request.form.get('tags') or 'remix').strip()
        if not prompt_ok(tags): return f'Prompt too long (max {MAX_BEAT_DESC_CHARS} chars)', 400

        gen = MUSICGEN.generate([f'remix from prompt: {tags}'])
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            MUSICGEN.save_wav(gen[0], tmp.name)
            y_new, sr = librosa.load(tmp.name, sr=None, mono=True)
        y_new = song_cap(y_new, sr)

        new = _save_new_song(s.user_id, f'Remix_{s.id}', y_new, sr, s.tags)
        return f'✅ Remixed → {new.title}'

    # --------- Cover % reinterpretation (1 credit) ----------
    @app.post('/api/song/cover/<int:song_id>')
    def api_cover(song_id):
        chk = ensure_np()
        if chk: return chk
        fail = deduct_credit_or_block()
        if fail: return fail
        s, path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404

        pct = float(request.form.get('percent','35')); pct = max(0.0, min(100.0, pct))
        alpha = pct/100.0
        y, sr = librosa.load(path, sr=None, mono=True)

        # Light DSP reinterpretation with optional MusicGen blending
        y1 = librosa.effects.pitch_shift(y, sr, n_steps=(alpha*3.0))
        tempo_rate = 1.0 + (0.12 * (2*alpha - 1.0))
        if tempo_rate <= 0: tempo_rate = 1.0
        y1 = librosa.effects.time_stretch(y1, tempo_rate)
        y1 = np.tanh(librosa.util.normalize(y1) * (1.0 + 0.6*alpha))

        # Optional MusicGen blend for >15%
        try:
            from audiocraft.models import MusicGen
            MG = MusicGen.get_pretrained('facebook/musicgen-small'); MG.set_generation_params(duration=20)
            if alpha > 0.15:
                gen = MG.generate([f'inspired {s.tags or "ambient"} cover'])
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    MG.save_wav(gen[0], tmp.name)
                    yg, srg = librosa.load(tmp.name, sr=sr, mono=True)
                yg = librosa.util.fix_length(yg, len(y1))
                y1 = librosa.util.normalize(y1*(1.0 - 0.4*alpha) + yg*(0.5*alpha))
        except Exception:
            pass

        # Fix final length and cap
        target = int(len(y) / tempo_rate)
        y1 = librosa.util.fix_length(y1, target)
        y1 = song_cap(y1, sr)

        new = _save_new_song(s.user_id, f'Cover{int(pct)}_{s.id}', y1, sr, s.tags)
        return f'✅ Cover {int(pct)}% → {new.title}'

    # --------- Make instrumental (1 credit) ----------
    @app.post('/api/song/mute-vocals/<int:song_id>')
    def api_mute_vocals(song_id):
        chk = ensure_np()
        if chk: return chk
        if not DEMUCS_OK: return 'Demucs not installed. pip install demucs', 501
        fail = deduct_credit_or_block()
        if fail: return fail
        s, base_path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404

        with tempfile.TemporaryDirectory() as work:
            wav_src = base_path
            if not base_path.lower().endswith('.wav'):
                wav_src = os.path.join(work, 'src.wav')
                subprocess.run(['ffmpeg','-y','-i', base_path, wav_src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            from demucs.separate import main as demucs_separate
            demucs_separate(['--two-stems=vocals','-o', work, wav_src])
            inst_path=None
            for root,_,files in os.walk(work):
                for f in files:
                    name=f.lower()
                    if name.endswith('.wav') and ('no_vocals' in name or 'instrumental' in name or 'other' in name):
                        inst_path=os.path.join(root,f)
            if not inst_path: return 'Stems not produced', 500
            y, sr = librosa.load(inst_path, sr=None, mono=True)
            y = song_cap(y, sr)
            new = _save_new_song(s.user_id, f'Instrumental_{s.id}', y, sr, s.tags)
            return f'✅ Instrumental → {new.title}'

    # --------- Gender swap (1 credit) ----------
    @app.post('/api/song/gender-swap/<int:song_id>')
    def api_gender_swap(song_id):
        chk = ensure_np()
        if chk: return chk
        if not PARSELMOUTH_OK: return 'praat-parselmouth not installed', 501
        if not DEMUCS_OK: return 'Demucs not installed', 501
        fail = deduct_credit_or_block()
        if fail: return fail
        s, base_path = _song_path(song_id)
        if not s or s.user_id != current_user().id: return 'Not found', 404

        target = (request.form.get('target') or 'female').strip().lower()
        strength = (request.form.get('strength') or 'medium').strip().lower()

        def gender_params(target: str, strength: str):
            s_map = {'light':0.6,'medium':1.0,'strong':1.4}; k = s_map.get(strength,1.0)
            if target=='female':
                formant_ratio = 1.15 + 0.05*k; pitch_semi = 2.0 + 1.0*k; range_ratio = 1.05 + 0.05*k
            else:
                formant_ratio = 0.90 - 0.05*(k-1.0); pitch_semi = -(2.0 + 1.0*k); range_ratio = 0.95 - 0.05*(k-1.0)
            return float(formant_ratio), float(pitch_semi), float(range_ratio)

        def praat_gender_shift(y, sr, target, strength):
            import parselmouth
            snd = parselmouth.Sound(y, sampling_frequency=sr)
            f0_min, f0_max = 75, 400
            formant_ratio, pitch_semi, range_ratio = gender_params(target, strength)
            base_median = 165.0
            new_pitch_median = base_median * (2.0 ** (pitch_semi/12.0))
            out = parselmouth.praat.call(snd, 'Change gender', f0_min, f0_max, formant_ratio, new_pitch_median, range_ratio, 1.0)
            return out.values.flatten().astype(np.float32)

        with tempfile.TemporaryDirectory() as work:
            wav_src = base_path
            if not base_path.lower().endswith('.wav'):
                wav_src = os.path.join(work, 'src.wav')
                subprocess.run(['ffmpeg','-y','-i', base_path, wav_src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            from demucs.separate import main as demucs_separate
            demucs_separate(['--two-stems=vocals','-o', work, wav_src])
            v_path, inst_path = None, None
            for root,_,files in os.walk(work):
                for f in files:
                    name=f.lower(); fp=os.path.join(root,f)
                    if name.endswith('.wav') and 'vocals' in name: v_path=fp
                    if name.endswith('.wav') and ('no_vocals' in name or 'instrumental' in name or 'other' in name): inst_path=fp
            if not v_path or not inst_path: return 'Stems not produced', 500

            v, sr = librosa.load(v_path, sr=None, mono=True)
            inst, sri = librosa.load(inst_path, sr=None, mono=True)
            if sri!=sr: inst = librosa.resample(inst, sri, sr)
            v2 = praat_gender_shift(v, sr, target, strength)
            v2 = librosa.util.normalize(v2) * 0.9
            inst = librosa.util.fix_length(inst, len(v2))
            y_out = librosa.util.normalize(inst*0.9 + v2*1.0)
            y_out = song_cap(y_out, sr)

        new = _save_new_song(s.user_id, f'Gender_{target}_{s.id}', y_out, sr, s.tags)
        return f'✅ Swapped vocals to {target} → {new.title}'