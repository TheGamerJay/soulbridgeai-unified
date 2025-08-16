// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyA8D4APGQRzuLI5cHgQHHdAqLvHglfY75U",
  authDomain: "soulbridgeai-admin.firebaseapp.com",
  projectId: "soulbridgeai-admin",
  storageBucket: "soulbridgeai-admin.firebasestorage.app",
  messagingSenderId: "873585500645",
  appId: "1:873585500645:web:c410f0960665a55e238f0c"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export default app;