// SoulBridge AI - Mini Studio API
// Professional music production with real AI models: MusicGen, DiffSinger, OpenAI
// Integrates with SoulBridge authentication and credit system

import express from "express";
import fileUpload from "express-fileupload";
import { readFileSync, createWriteStream, statSync } from "fs";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import pg from "pg";
import { v4 as uuid } from "uuid";
import fetch from "node-fetch";
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const app = express();
app.use(express.json({ limit: "25mb" }));
app.use(fileUpload());

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const STORAGE_DIR = process.env.STORAGE_DIR || "/data/assets";
await mkdir(STORAGE_DIR, { recursive: true });

// Initialize database schema
try {
  await pool.query(readFileSync(new URL("../db.sql", import.meta.url), "utf8"));
  console.log("✅ Database initialized successfully");
} catch (error) {
  console.error("❌ Database initialization failed:", error);
}

// SoulBridge authentication middleware (replaces demo user)
function authenticate(req, res, next) {
  // Get user ID from SoulBridge session header
  const userId = req.headers['x-user-id'];
  if (!userId) {
    return res.status(401).json({ error: "Authentication required" });
  }
  req.user = { id: userId };
  next();
}

app.use(authenticate);

// User and credits management
async function ensureUser(userId) {
  await pool.query(
    "INSERT INTO users(id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
    [userId]
  );
  await pool.query(
    "INSERT INTO credits(user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
    [userId]
  );
}

async function creditsOf(userId) {
  await ensureUser(userId);
  const { rows } = await pool.query(
    "SELECT credits_remaining FROM credits WHERE user_id=$1",
    [userId]
  );
  return rows[0].credits_remaining;
}

async function deductCredits(userId, amount) {
  const { rows } = await pool.query(
    `UPDATE credits SET credits_remaining = credits_remaining - $2
     WHERE user_id=$1 AND credits_remaining >= $2 RETURNING credits_remaining`,
    [userId, amount]
  );
  return rows.length ? rows[0].credits_remaining : null;
}

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ 
    status: "healthy", 
    service: "soulbridge-mini-studio-api",
    timestamp: new Date().toISOString()
  });
});

// Project management
app.post("/api/projects/ensure", async (req, res) => {
  try {
    await ensureUser(req.user.id);
    const { rows } = await pool.query(
      "SELECT id FROM projects WHERE user_id=$1 ORDER BY created_at DESC LIMIT 1",
      [req.user.id]
    );
    if (rows.length) return res.json({ project_id: rows[0].id });
    
    const id = uuid();
    await pool.query("INSERT INTO projects(id,user_id,name) VALUES ($1,$2,$3)", [
      id,
      req.user.id,
      "My Studio Project",
    ]);
    res.json({ project_id: id });
  } catch (error) {
    console.error("Project creation error:", error);
    res.status(500).json({ error: "Failed to create project" });
  }
});

// Credits endpoint
app.get("/api/credits", async (req, res) => {
  try {
    const credits = await creditsOf(req.user.id);
    res.json({ credits_remaining: credits });
  } catch (error) {
    console.error("Credits fetch error:", error);
    res.status(500).json({ error: "Failed to get credits" });
  }
});

// Asset upload
app.post("/api/assets/upload", async (req, res) => {
  try {
    const f = req.files?.file;
    const { project_id, kind } = req.body;
    
    if (!f) return res.status(400).json({ error: "No file provided" });
    if (!["lyrics", "beat", "midi"].includes(kind)) {
      return res.status(400).json({ error: "Invalid asset kind" });
    }

    const id = uuid();
    const ext = kind === "lyrics" ? ".txt" : (f.name.match(/\.[^.]+$/)?.[0] || "");
    const dest = path.join(STORAGE_DIR, `${id}${ext}`);
    
    await writeFile(dest, f.data);
    
    await pool.query(
      `INSERT INTO assets(id,project_id,user_id,kind,path,mime,bytes,origin)
       VALUES ($1,$2,$3,$4,$5,$6,$7,'external')`,
      [id, project_id, req.user.id, kind, dest, f.mimetype, f.size]
    );
    
    res.json({ assetId: id, origin: "external" });
  } catch (error) {
    console.error("Asset upload error:", error);
    res.status(500).json({ error: "Upload failed" });
  }
});

// Lyrics generation with OpenAI Responses API + Structured Outputs
app.post("/api/lyrics/generate", async (req, res) => {
  try {
    const cost = 5; // 5 artistic time credits
    if ((await deductCredits(req.user.id, cost)) === null) {
      return res.status(402).json({ error: "Insufficient credits" });
    }

    const { 
      project_id, 
      concept = "heartbreak to healing", 
      bpm = 94, 
      key_hint = "A minor", 
      language = "spanglish" 
    } = req.body;
    
    const schema = {
      type: "object",
      properties: {
        title: { type: "string" },
        language: { type: "string" },
        tempo_hint_bpm: { type: "integer" },
        key_hint: { type: "string" },
        sections: {
          type: "array",
          items: {
            type: "object",
            properties: {
              type: { type: "string" },
              bars: { type: "integer" },
              lyrics: { type: "string" }
            },
            required: ["type","bars","lyrics"]
          }
        }
      },
      required: ["title","language","tempo_hint_bpm","key_hint","sections"]
    };

    const resp = await openai.responses.create({
      model: "gpt-4o",
      input: [
        { role: "system", content: "You are a professional songwriter. Create structured lyrics with sections like intro, verse, chorus, bridge, outro. Output ONLY valid JSON matching the schema." },
        { role: "user", content: `
Concept: ${concept}
Language: ${language}
Target BPM: ${bpm}
Key: ${key_hint}
Structure: Create intro(4 bars), verse(16 bars), pre-chorus(8 bars), chorus(8 bars), verse(16 bars), bridge(8 bars), outro(4 bars)
Make it emotionally resonant and memorable.` }
      ],
      response_format: { 
        type: "json_schema", 
        json_schema: { name: "Lyrics", schema } 
      }
    });

    const payload = resp.output[0].content[0].text;
    const id = uuid();
    const dest = path.join(STORAGE_DIR, `${id}.json`);
    
    await writeFile(dest, payload);
    const bytes = statSync(dest).size;
    
    await pool.query(
      `INSERT INTO assets(id,project_id,user_id,kind,path,mime,bytes,origin)
       VALUES ($1,$2,$3,'lyrics',$4,'application/json',$5,'internal')`,
      [id, project_id, req.user.id, dest, bytes]
    );
    
    res.json({ assetId: id });
  } catch (error) {
    console.error("Lyrics generation error:", error);
    res.status(500).json({ error: "Lyrics generation failed" });
  }
});

// Beat composition with MusicGen + MIDI stems
app.post("/api/beats/compose", async (req, res) => {
  try {
    const cost = 10; // 10 artistic time credits
    if ((await deductCredits(req.user.id, cost)) === null) {
      return res.status(402).json({ error: "Insufficient credits" });
    }

    const { 
      project_id, 
      prompt = "melodic trap beat, punchy drums, warm bass", 
      bpm = 94, 
      key = "A minor", 
      seconds = 15, 
      demucs = false 
    } = req.body;

    const response = await fetch(`${process.env.BEATS_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, bpm, key, seconds, demucs })
    });

    if (!response.ok) {
      return res.status(500).json({ error: "Beat service failed" });
    }

    // Save beat zip to storage
    const id = uuid();
    const dest = path.join(STORAGE_DIR, `${id}.zip`);
    const file = createWriteStream(dest);
    
    await new Promise((resolve, reject) => {
      response.body.pipe(file);
      response.body.on("error", reject);
      file.on("finish", resolve);
    });
    
    const bytes = statSync(dest).size;

    await pool.query(
      `INSERT INTO assets(id,project_id,user_id,kind,path,mime,bytes,origin)
       VALUES ($1,$2,$3,'beat',$4,'application/zip',$5,'internal')`,
      [id, project_id, req.user.id, dest, bytes]
    );

    res.json({ assetId: id });
  } catch (error) {
    console.error("Beat composition error:", error);
    res.status(500).json({ error: "Beat composition failed" });
  }
});

// Vocal generation with DiffSinger
app.post("/api/vocals/sing", async (req, res) => {
  try {
    const { project_id, lyrics_asset_id, beat_asset_id, midi_asset_id, bpm = 94 } = req.body;

    // Get asset paths
    const [lr, bt, md] = await Promise.all([
      lyrics_asset_id ? pool.query("SELECT path FROM assets WHERE id=$1 AND user_id=$2 AND kind='lyrics'", [lyrics_asset_id, req.user.id]) : null,
      beat_asset_id   ? pool.query("SELECT path FROM assets WHERE id=$1 AND user_id=$2 AND kind='beat'", [beat_asset_id, req.user.id]) : null,
      midi_asset_id   ? pool.query("SELECT path FROM assets WHERE id=$1 AND user_id=$2 AND kind='midi'", [midi_asset_id, req.user.id]) : null
    ]);

    const hasLyrics = !!(lr && lr.rowCount);
    const hasBeat   = !!(bt && bt.rowCount);

    // Dynamic pricing: 10 base + 5 for missing lyrics + 10 for missing beat
    const cost = 10 + (hasLyrics ? 0 : 5) + (hasBeat ? 0 : 10);
    
    if ((await deductCredits(req.user.id, cost)) === null) {
      return res.status(402).json({ error: "Insufficient credits" });
    }

    const payload = {
      bpm,
      lyrics_json_path: hasLyrics ? lr.rows[0].path : null,
      beat_zip_path: hasBeat ? bt.rows[0].path : null,
      midi_path: (md && md.rowCount) ? md.rows[0].path : null
    };

    const response = await fetch(`${process.env.VOCALS_URL}/sing`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      return res.status(500).json({ error: "Vocal service failed" });
    }

    // Save vocal wav to storage
    const id = uuid();
    const dest = path.join(STORAGE_DIR, `${id}.wav`);
    const file = createWriteStream(dest);
    
    await new Promise((resolve, reject) => {
      response.body.pipe(file);
      response.body.on("error", reject);
      file.on("finish", resolve);
    });
    
    const bytes = statSync(dest).size;

    await pool.query(
      `INSERT INTO assets(id,project_id,user_id,kind,path,mime,bytes,origin)
       VALUES ($1,$2,$3,'vocal',$4,'audio/wav',$5,'internal')`,
      [id, project_id, req.user.id, dest, bytes]
    );

    // Record vocal job
    await pool.query(
      `INSERT INTO vocal_jobs(id, project_id, user_id, lyrics_asset, beat_asset, midi_asset, cost_credits, status, result_asset)
       VALUES ($1,$2,$3,$4,$5,$6,$7,'done',$8)`,
      [uuid(), project_id, req.user.id, lyrics_asset_id || null, beat_asset_id || null, midi_asset_id || null, cost, id]
    );

    res.json({ assetId: id, cost });
  } catch (error) {
    console.error("Vocal generation error:", error);
    res.status(500).json({ error: "Vocal generation failed" });
  }
});

// Start server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`🎵 SoulBridge Mini Studio API listening on port ${PORT}`);
  console.log(`🔗 OpenAI API: ${process.env.OPENAI_API_KEY ? "✅ Connected" : "❌ Missing"}`);
  console.log(`🎹 Beats URL: ${process.env.BEATS_URL}`);
  console.log(`🎤 Vocals URL: ${process.env.VOCALS_URL}`);
});