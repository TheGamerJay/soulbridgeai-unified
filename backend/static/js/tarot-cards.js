// Tarot Card Image Path Helper
// Use this function to get the correct path for tarot card images

/**
 * Generate the correct image path for a tarot card
 * @param {string} name - The card name (e.g., "The Fool", "Ace of Wands")
 * @returns {string} - The path to the card image
 */
const imgPath = (name) => `/static/cards/${name.replace(/ /g, "_")}.jpg`;

/**
 * Generate the correct image path with fallback
 * @param {string} name - The card name
 * @returns {string} - The path to the card image or placeholder
 */
const getCardImagePath = (name) => {
    if (!name) return '/static/cards/placeholder.jpg';
    return `/static/cards/${name.replace(/ /g, "_").replace(/[^a-zA-Z0-9_]/g, "")}.jpg`;
};

/**
 * Preload a tarot card image
 * @param {string} cardName - The card name
 * @returns {Promise} - Resolves when image loads, rejects if fails
 */
const preloadCardImage = (cardName) => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Failed to load card: ${cardName}`));
        img.src = imgPath(cardName);
    });
};

/**
 * Create a card image element
 * @param {Object} card - Card object with name, position, reversed properties
 * @returns {HTMLElement} - Image element for the card
 */
const createCardImage = (card) => {
    const img = document.createElement('img');
    img.src = imgPath(card.name);
    img.alt = card.name;
    img.className = 'tarot-card';
    
    if (card.reversed) {
        img.classList.add('reversed');
    }
    
    img.onerror = () => {
        img.src = '/static/cards/placeholder.jpg';
    };
    
    return img;
};

// Make functions globally available
window.imgPath = imgPath;
window.getCardImagePath = getCardImagePath;
window.preloadCardImage = preloadCardImage;
window.createCardImage = createCardImage;