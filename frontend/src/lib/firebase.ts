// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBS1gB1SLRrHmcL2pVzqU47oTgNoFFYnmw",
  authDomain: "rideweave-8b2ab.firebaseapp.com",
  projectId: "rideweave-8b2ab",
  storageBucket: "rideweave-8b2ab.firebasestorage.app",
  messagingSenderId: "487004699471",
  appId: "1:487004699471:web:2b55978d01ead4f381633a",
  measurementId: "G-ZLWN1LZWKL"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const analytics = typeof window !== 'undefined' ? getAnalytics(app) : null;
export default app;
