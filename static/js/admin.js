document.addEventListener("DOMContentLoaded", () => {
  const toastEl = document.getElementById("toast");

  loadStatus();
  loadFAQList();

  // Knowledge text form
  document.getElementById("knowledge-text-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("k-title").value.trim();
    const content = document.getElementById("k-content").value.trim();
    if (!title || !content) return;

    try {
      const res = await fetch("/api/knowledge/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      });
      if (res.ok) {
        showToast("ナレッジを登録しました");
        document.getElementById("k-title").value = "";
        document.getElementById("k-content").value = "";
        loadStatus();
      } else {
        const data = await res.json();
        showToast(data.detail || "エラーが発生しました");
      }
    } catch {
      showToast("通信エラーが発生しました");
    }
  });

  // Knowledge file form
  document.getElementById("knowledge-file-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("k-file");
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
      const res = await fetch("/api/knowledge/file", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        showToast("ファイルからナレッジを登録しました");
        fileInput.value = "";
        loadStatus();
      } else {
        const data = await res.json();
        showToast(data.detail || "エラーが発生しました");
      }
    } catch {
      showToast("通信エラーが発生しました");
    }
  });

  // Clear knowledge
  document.getElementById("clear-knowledge-btn").addEventListener("click", async () => {
    if (!confirm("すべてのナレッジを削除しますか？")) return;
    try {
      await fetch("/api/knowledge", { method: "DELETE" });
      showToast("ナレッジを削除しました");
      loadStatus();
    } catch {
      showToast("通信エラーが発生しました");
    }
  });

  // FAQ form
  document.getElementById("faq-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = document.getElementById("faq-question").value.trim();
    const answer = document.getElementById("faq-answer").value.trim();
    if (!question || !answer) return;

    try {
      const res = await fetch("/api/faq", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, answer }),
      });
      if (res.ok) {
        showToast("FAQを追加しました");
        document.getElementById("faq-question").value = "";
        document.getElementById("faq-answer").value = "";
        loadFAQList();
      } else {
        const data = await res.json();
        showToast(data.detail || "エラーが発生しました");
      }
    } catch {
      showToast("通信エラーが発生しました");
    }
  });

  async function loadStatus() {
    try {
      const res = await fetch("/api/knowledge/status");
      const data = await res.json();
      document.getElementById("knowledge-status").textContent =
        `登録済みチャンク数: ${data.document_count}`;
    } catch {
      document.getElementById("knowledge-status").textContent = "ステータス取得エラー";
    }
  }

  async function loadFAQList() {
    try {
      const res = await fetch("/api/faq");
      const list = await res.json();
      const ul = document.getElementById("faq-list");
      ul.innerHTML = "";
      if (list.length === 0) {
        ul.innerHTML = "<li>FAQはまだ登録されていません</li>";
        return;
      }
      list.forEach((item) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <div>
            <div class="faq-q">${escapeHtml(item.question)}</div>
            <div class="faq-a">${escapeHtml(item.answer)}</div>
          </div>
          <button class="btn btn-danger btn-sm" onclick="deleteFAQ(${item.id})">削除</button>
        `;
        ul.appendChild(li);
      });
    } catch {
      // ignore
    }
  }

  window.deleteFAQ = async (index) => {
    if (!confirm("このFAQを削除しますか？")) return;
    try {
      await fetch(`/api/faq/${index}`, { method: "DELETE" });
      showToast("FAQを削除しました");
      loadFAQList();
    } catch {
      showToast("通信エラーが発生しました");
    }
  };

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("visible");
    setTimeout(() => toastEl.classList.remove("visible"), 2500);
  }
});
