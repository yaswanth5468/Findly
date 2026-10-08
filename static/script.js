function formatResultCard(result) {
    const card = document.createElement("div");
    card.className = "result-card";

    const values = Array.isArray(result && result.data) ? result.data : [String(result)];
    const name = values[0] || "Unnamed result";
    const extension = values[1] || "";
    const size = values[2] || "";
    const path = values[3] || values[0] || "";

    const meta = document.createElement("div");
    meta.className = "result-meta";

    const badge = document.createElement("span");
    badge.className = "file-badge";
    badge.textContent = extension ? extension.replace(".", "").toUpperCase() || "FILE" : "FILE";

    const sizeLabel = document.createElement("span");
    sizeLabel.className = "file-size";
    sizeLabel.textContent = size && size !== "" ? `${size} MB` : "File";

    meta.appendChild(badge);
    meta.appendChild(sizeLabel);

    const title = document.createElement("h3");
    title.className = "result-name";
    title.textContent = name;

    const location = document.createElement("p");
    location.className = "result-path";
    location.textContent = path;

    card.appendChild(meta);
    card.appendChild(title);
    card.appendChild(location);
    return card;
}

async function searchFiles(queryOverride) {
    const input = document.getElementById("searchInput");
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    const query = (queryOverride || input.value).trim();

    if (!query) {
        status.textContent = "Enter something to search.";
        return;
    }

    status.textContent = "Searching...";
    results.innerHTML = "";

    try {
        const response = await fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (!data.success) {
            status.textContent = data.message || "Search failed.";
            return;
        }

        status.textContent = data.count
            ? `Showing ${data.count} result${data.count === 1 ? "" : "s"}`
            : "No results found.";

        if (!data.results.length) {
            const empty = document.createElement("div");
            empty.className = "result-card empty";
            empty.textContent = "No matching files found. Try a broader search like 'photos from 2025' or 'large videos'.";
            results.appendChild(empty);
            return;
        }

        data.results.forEach(function(result) {
            results.appendChild(formatResultCard(result));
        });

        if ("speechSynthesis" in window) {
            const utterance = new SpeechSynthesisUtterance(
                `I found ${data.count} results for ${query}`
            );
            speechSynthesis.cancel();
            speechSynthesis.speak(utterance);
        }

    } catch (error) {
        console.error("Search error:", error);
        status.textContent = "Could not connect to Findly.";
    }
}

function startVoiceSearch() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceButton = document.getElementById("voiceButton");
    const input = document.getElementById("searchInput");
    const status = document.getElementById("status");

    if (!SpeechRecognition) {
        status.textContent = "Voice input is not supported in this browser.";
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        voiceButton.disabled = true;
        status.textContent = "Listening...";
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        status.textContent = "Voice query captured: " + transcript;
        searchFiles(transcript);
    };

    recognition.onerror = function() {
        status.textContent = "Voice input failed. Please try again.";
        voiceButton.disabled = false;
    };

    recognition.onend = function() {
        voiceButton.disabled = false;
    };

    recognition.start();
}

document.getElementById("searchInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        searchFiles();
    }
});

document.querySelectorAll(".chip").forEach(function(button) {
    button.addEventListener("click", function() {
        const input = document.getElementById("searchInput");
        input.value = button.dataset.query;
        searchFiles(button.dataset.query);
    });
});