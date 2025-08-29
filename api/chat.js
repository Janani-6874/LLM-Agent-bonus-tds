// /api/chat.js
import OpenAI from "openai";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { messages, model } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: "Invalid request. 'messages' array required." });
    }

    //  Use your Vercel environment variable, not exposed to frontend
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });

    const completion = await openai.chat.completions.create({
      model: model || "gpt-4o-mini",
      messages,
    });

    const reply = completion.choices[0].message.content;

    return res.status(200).json({ reply });
  } catch (err) {
    console.error("Error in /api/chat:", err);
    return res.status(500).json({ error: "Internal Server Error" });
  }
}

