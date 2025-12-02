import { GoogleGenAI } from "@google/genai";

// Initialize the client
// In a real app, ensure process.env.API_KEY is set.
const apiKey = process.env.API_KEY || 'dummy_key'; 
const ai = new GoogleGenAI({ apiKey });

export const sendMessageToGemini = async (prompt: string, modelName: string = 'gemini-2.5-flash'): Promise<string> => {
  try {
    // Determine model based on internal logic if needed, but defaulting to Flash 2.5 as requested by system prompt standards
    // If the UI is in "Thinking" mode (which we might map to a specific model or config), we handle it here.
    
    // Note: 'gemini-2.5-flash-thinking' isn't a standard public model alias yet in the SDK docs provided, 
    // so we use 'gemini-2.5-flash' but with a higher token limit if we were doing real "thinking".
    
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash', 
      contents: prompt,
    });

    return response.text || "No response text found.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Przepraszam, wystąpił błąd podczas łączenia z usługą.";
  }
};