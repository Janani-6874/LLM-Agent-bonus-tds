// agent.js

// --- UI Helpers ---
function addMessage(role, text) {
  const chatWindow = document.getElementById("chat-window");
  const msg = document.createElement("div");
  msg.className = `message ${role}`;
  msg.textContent = `${role.toUpperCase()}: ${text}`;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTypingIndicator(show) {
  const indicator = document.getElementById("typing-indicator");
  if (!indicator) return;

  if (show) {
    indicator.style.display = "block";
  } else {
    indicator.style.display = "none";
  }
}

// --- OpenAI API Call ---
async function callOpenAI(apiKey, model, messages) {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: model || "gpt-4o-mini", // default to gpt-4o-mini
      messages: messages,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`OpenAI API error (${response.status}): ${errText}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

// --- Send User Message ---
async function sendMessage(userText) {
  const apiKey = localStorage.getItem("openai_api_key");
  if (!apiKey) {
    alert("⚠️ Please set your API key in Settings first.");
    return;
  }

  const model = document.getElementById("model-name")
    ? document.getElementById("model-name").value
    : "gpt-4o-mini";

  const messages = [{ role: "user", content: userText }];

  try {
    showTypingIndicator(true);
    const reply = await callOpenAI(apiKey, model, messages);
    addMessage("assistant", reply);
  } catch (err) {
    addMessage("system", "⚠️ " + err.message);
  } finally {
    showTypingIndicator(false);
  }
}

// --- Event Listeners ---
document.addEventListener("DOMContentLoaded", () => {
  // Handle send button
  const sendBtn = document.getElementById("send-message");
  if (sendBtn) {
    sendBtn.addEventListener("click", () => {
      const userInput = document.getElementById("user-input").value.trim();
      if (!userInput) return;
      addMessage("user", userInput);
      document.getElementById("user-input").value = "";
      sendMessage(userInput);
    });
  }

  // Handle settings save
  const saveBtn = document.getElementById("save-settings");
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const apiKeyInput = document.getElementById("api-key").value.trim();
      if (!apiKeyInput) {
        alert("⚠️ Please enter a valid API key.");
        return;
      }
      localStorage.setItem("openai_api_key", apiKeyInput);
      alert("✅ API key saved locally!");
    });
  }

  // Initialize chat window
  addMessage("system", "LLM TDS ready. Please enter your OpenAI API key in Settings ⚙️ to start chatting!");
});
