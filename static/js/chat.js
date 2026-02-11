document.addEventListener("DOMContentLoaded", () => {
  const messagesEl = document.getElementById("chat-messages");
  const inputEl = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const faqButtonsEl = document.getElementById("faq-buttons");
  const faqSection = document.getElementById("faq-section");
  const typingIndicator = document.getElementById("typing-indicator");

  loadFAQ();

  sendBtn.addEventListener("click", () => sendMessage());
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.isComposing) sendMessage();
  });

  function addMessage(text, role) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (role === "bot") {
      div.innerHTML = `<span class="sender-label">ソフィアAI</span>${escapeHtml(text)}`;
    } else {
      div.textContent = text;
    }
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  async function sendMessage(overrideText) {
    const text = overrideText || inputEl.value.trim();
    if (!text) return;

    inputEl.value = "";
    addMessage(text, "user");

    sendBtn.disabled = true;
    typingIndicator.classList.add("visible");
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      if (res.ok) {
        addMessage(data.response, "bot");
      } else {
        addMessage(data.detail || "エラーが発生しました。", "bot");
      }
    } catch {
      addMessage("通信エラーが発生しました。しばらくしてからお試しください。", "bot");
    } finally {
      typingIndicator.classList.remove("visible");
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  async function loadFAQ() {
    try {
      const res = await fetch("/api/faq");
      const faqList = await res.json();
      if (faqList.length === 0) {
        faqSection.style.display = "none";
        return;
      }
      faqSection.style.display = "block";
      faqButtonsEl.innerHTML = "";
      faqList.forEach((item) => {
        const btn = document.createElement("button");
        btn.className = "faq-btn";
        btn.textContent = item.question;
        btn.addEventListener("click", () => {
          sendMessage(item.question);
        });
        faqButtonsEl.appendChild(btn);
      });
    } catch {
      faqSection.style.display = "none";
    }
  }

  // Welcome message
  addMessage(
    "こんにちは！株式会社ソフィアのAIアシスタントです。\nご質問がありましたらお気軽にどうぞ。\n下のボタンからよくある質問もお選びいただけます。",
    "bot"
  );
});
