// API Configuration
const RAILWAY_BACKEND_URL = ""; // Update with your Railway public URL
let API_BASE;

if (RAILWAY_BACKEND_URL && RAILWAY_BACKEND_URL.trim() !== "") {
    API_BASE = RAILWAY_BACKEND_URL.trim();
} else if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    API_BASE = "http://localhost:5000";
} else {
    API_BASE = window.location.origin;
}

console.log("API Base:", API_BASE);

let screeningResults = [];

// Event Listeners
document.getElementById("screen_btn").addEventListener("click", screenResumes);
document.getElementById("export_csv_btn").addEventListener("click", exportCSV);
document.getElementById("export_excel_btn").addEventListener("click", exportExcel);

async function screenResumes() {
    const jdFile = document.getElementById("jd_file").files[0];
    const jdText = document.getElementById("jd_text").value.trim();
    const resumeFiles = document.getElementById("resume_files").files;

    if (!jdFile && !jdText) {
        alert("⚠️ Please provide a job description (file or text)");
        return;
    }

    if (resumeFiles.length === 0) {
        alert("⚠️ Please select at least one resume");
        return;
    }

    const formData = new FormData();
    
    if (jdFile) {
        formData.append("jd_file", jdFile);
    } else {
        // Create a temporary file from text
        const blob = new Blob([jdText], { type: "text/plain" });
        formData.append("jd_file", blob, "jd.txt");
    }

    for (let file of resumeFiles) {
        formData.append("resume_files", file);
    }

    try {
        document.getElementById("loading").style.display = "block";
        document.getElementById("results_section").style.display = "block";
        document.getElementById("results_table").innerHTML = "";

        const response = await fetch(`${API_BASE}/screen`, {
            method: "POST",
            body: formData,
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            screeningResults = data.results;
            displayResults(data);
            document.getElementById("export_csv_btn").disabled = false;
            document.getElementById("export_excel_btn").disabled = false;
        } else {
            alert(`❌ Error: ${data.error}`);
        }
    } catch (error) {
        console.error("Error:", error);
        alert(`❌ Failed to screen resumes: ${error.message}`);
    } finally {
        document.getElementById("loading").style.display = "none";
    }
}

function displayResults(data) {
    const html = `
        <div class="alert alert-info">
            <strong>Total Processed:</strong> ${data.total} | 
            <strong>Weights:</strong> TF-IDF ${(data.weights.bert * 100).toFixed(0)}% + Supabase ${(data.weights.supabase * 100).toFixed(0)}%
        </div>
        <table class="table table-striped table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Filename</th>
                    <th>TF-IDF Score</th>
                    <th>Supabase Score</th>
                    <th>Hybrid Score</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
                ${data.results.map((result, idx) => `
                    <tr>
                        <td><strong>#${idx + 1}</strong></td>
                        <td>${result.candidate_name}</td>
                        <td>${result.filename}</td>
                        <td><span class="badge bg-primary">${result.bert_score}</span></td>
                        <td><span class="badge bg-success">${result.supabase_score}</span></td>
                        <td><span class="badge bg-danger" style="font-size: 1.1em; padding: 0.5em 0.8em;">${result.hybrid_score}</span></td>
                        <td>${getRecommendationBadge(result.recommendation)}</td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
        ${data.errors.length > 0 ? `
            <div class="alert alert-warning">
                <strong>Errors:</strong>
                <ul>
                    ${data.errors.map(err => `<li>${err}</li>`).join("")}
                </ul>
            </div>
        ` : ""}
    `;
    document.getElementById("results_table").innerHTML = html;
}

function getRecommendationBadge(recommendation) {
    const badgeClass = recommendation === "Good Match" ? "bg-success" : recommendation === "Moderate Match" ? "bg-warning" : "bg-danger";
    return `<span class="badge ${badgeClass}">${recommendation}</span>`;
}

function exportCSV() {
    if (screeningResults.length === 0) {
        alert("No results to export");
        return;
    }

    const headers = ["Rank", "Candidate", "Filename", "TF-IDF Score", "Supabase Score", "Hybrid Score", "Recommendation"];
    const rows = screeningResults.map((result, idx) => [
        idx + 1,
        result.candidate_name,
        result.filename,
        result.bert_score,
        result.supabase_score,
        result.hybrid_score,
        result.recommendation
    ]);

    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(",")).join("\n");
    
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resume-screening-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

function exportExcel() {
    if (screeningResults.length === 0) {
        alert("No results to export");
        return;
    }

    const ws_name = "Screening Results";
    const wb = XLSX.utils.book_new();
    
    const data = screeningResults.map((result, idx) => ({
        "Rank": idx + 1,
        "Candidate": result.candidate_name,
        "Filename": result.filename,
        "TF-IDF Score": result.bert_score,
        "Supabase Score": result.supabase_score,
        "Hybrid Score": result.hybrid_score,
        "Recommendation": result.recommendation
    }));

    const ws = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(wb, ws, ws_name);
    XLSX.writeFile(wb, `resume-screening-${new Date().toISOString().split('T')[0]}.xlsx`);
}
