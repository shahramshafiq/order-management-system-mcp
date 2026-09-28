const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");
const button = form.querySelector("button");

function addMessage(text, role, toolCalls) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  if (toolCalls && toolCalls.length > 0) {
    const toolsEl = document.createElement("div");
    toolsEl.className = "tool-calls";
    toolsEl.innerHTML = "tools used: " + toolCalls.map((t) => `<span class="tool-tag">${t}</span>`).join("");
    wrapper.appendChild(toolsEl);
  }

  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage(text) {
  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "The assistant returned an error.");
  }
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";
  input.disabled = true;
  button.disabled = true;

  try {
    const data = await sendMessage(text);
    addMessage(data.answer, "assistant", data.tool_calls);
  } catch (err) {
    addMessage(err.message || "Could not reach the assistant.", "error");
  } finally {
    input.disabled = false;
    button.disabled = false;
    input.focus();
  }
});
