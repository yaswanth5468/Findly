async function searchFiles() {

    const input = document.getElementById("searchInput");
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    const query = input.value.trim();

    console.log("Search button clicked");
    console.log("Query:", query);

    if (!query) {
        status.textContent = "Enter something to search.";
        return;
    }

    status.textContent = "Searching...";
    results.innerHTML = "";

    try {

        console.log("Sending request to Flask...");

        const response = await fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query
            })
        });

        console.log("Flask response received");

        const data = await response.json();

        console.log("Response data:", data);

        if (!data.success) {

            status.textContent =
                data.message || "Search failed.";

            return;
        }

        status.textContent =
            "Results found: " + data.count;

        if (data.results.length === 0) {

            results.innerHTML = `
                <div class="result-card">
                    No matching files found.
                </div>
            `;

            return;
        }

        data.results.forEach(function(result) {

            const card = document.createElement("div");

            card.className = "result-card";

            card.textContent =
                result.data.join(" | ");

            results.appendChild(card);

        });

    } catch (error) {

        console.error("Search error:", error);

        status.textContent =
            "Could not connect to Findly.";

    }
}


document
    .getElementById("searchInput")
    .addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            searchFiles();
        }

    });