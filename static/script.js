document.addEventListener("DOMContentLoaded", () => {
    // ============ DOM ELEMENTS ============
    const uploadSection = document.getElementById("upload-section");
    const loadingSection = document.getElementById("loading-section");
    const errorSection = document.getElementById("error-section");
    const resultsContainer = document.getElementById("results-container");

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const browseBtn = document.getElementById("browse-btn");
    const fileChip = document.getElementById("file-chip");
    const fileChipName = document.getElementById("file-chip-name");
    const fileChipSize = document.getElementById("file-chip-size");
    const fileChipRemove = document.getElementById("file-chip-remove");
    const analyzeBtn = document.getElementById("analyze-btn");
    const uploadError = document.getElementById("upload-error");

    const loadingStatus = document.getElementById("loading-status");
    const loadingSubtext = document.getElementById("loading-subtext");
    const loadingStepEls = {
        upload: document.getElementById("step-upload"),
        parse: document.getElementById("step-parse"),
        extract: document.getElementById("step-extract"),
        analyze: document.getElementById("step-analyze"),
        report: document.getElementById("step-report"),
    };

    const errorTitle = document.getElementById("error-title");
    const errorMessage = document.getElementById("error-message");
    const errorRetryBtn = document.getElementById("error-retry-btn");

    const scoreDisplay = document.getElementById("score-display");
    const scoreRating = document.getElementById("score-rating");
    const scoreCircleFill = document.getElementById("score-circle-fill");
    const categoryScoreList = document.getElementById("category-score-list");

    const candidateName = document.getElementById("candidate-name");
    const candidateContact = document.getElementById("candidate-contact");
    const metaFilename = document.getElementById("meta-filename");
    const metaDate = document.getElementById("meta-date");
    const reportInterpretation = document.getElementById("report-interpretation");

    const overviewStrengths = document.getElementById("overview-strengths");
    const overviewIssues = document.getElementById("overview-issues");
    const overviewPriority = document.getElementById("overview-priority");

    const strengthsList = document.getElementById("strengths-list");

    const compatibilityChecksTable = document.getElementById("compatibility-checks-table");
    const compatReadiness = document.getElementById("compat-readiness");
    const compatFilters = document.querySelectorAll("#compat-filters .filter-chip");

    const completenessBar = document.getElementById("completeness-bar");
    const completenessText = document.getElementById("completeness-text");
    const completenessSectionsGrid = document.getElementById("completeness-sections-grid");

    const skillsDisplayContainer = document.getElementById("skills-display-container");
    const skillTabFilters = document.querySelectorAll("#skill-tab-filters .filter-chip");
    const keywordStrengthList = document.getElementById("keyword-strength-list");

    const achievementsCount = document.getElementById("achievements-count");
    const detectedAchievementsList = document.getElementById("detected-achievements-list");
    const actionSuggestionsList = document.getElementById("action-suggestions-list");

    const jsonAccordionBtn = document.getElementById("json-accordion-btn");
    const rawJsonBlock = document.getElementById("raw-json-block");
    const copyJsonBtn = document.getElementById("copy-json-btn");
    const resetBtn = document.getElementById("reset-btn");
    const newUploadBtn = document.getElementById("new-upload-btn");

    const explanationAccordionBtn = document.getElementById("explanation-accordion-btn");
    const weaknessFilters = document.querySelectorAll("#weakness-filters .filter-chip");
    const downloadPdfBtn = document.getElementById("download-pdf-btn");

    const extractedProfileContainer = document.getElementById("extracted-profile-container");

    let currentAnalysisData = null;
    let selectedFile = null;
    let activeCompatFilter = "all";
    let activeSkillTab = "categorized";
    let allWeaknesses = [];

    // ============ SCROLLSPY NAV ============
    const navLinks = document.querySelectorAll(".nav-link");
    function setupScrollSpy() {
        const sections = Array.from(navLinks)
            .map(link => document.getElementById(link.dataset.nav))
            .filter(Boolean);
        if (sections.length === 0) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    navLinks.forEach(l => l.classList.remove("active"));
                    const activeLink = document.querySelector(`.nav-link[data-nav="${entry.target.id}"]`);
                    if (activeLink) activeLink.classList.add("active");
                }
            });
        }, { rootMargin: "-40% 0px -50% 0px" });

        sections.forEach(s => observer.observe(s));
    }

    // ============ FILE SELECTION ============
    browseBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) selectFile(e.target.files[0]);
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) selectFile(e.dataTransfer.files[0]);
    });

    fileChipRemove.addEventListener("click", () => {
        selectedFile = null;
        fileInput.value = "";
        fileChip.classList.add("hidden");
        analyzeBtn.classList.add("hidden");
        hideUploadError();
    });

    function selectFile(file) {
        hideUploadError();
        const ext = file.name.split(".").pop().toLowerCase();
        if (!["pdf", "docx", "doc"].includes(ext)) {
            showUploadError("Please upload a PDF or DOCX file.");
            return;
        }
        if (file.size > 16 * 1024 * 1024) {
            showUploadError("File is too large. Maximum size is 16 MB.");
            return;
        }

        selectedFile = file;
        fileChipName.textContent = file.name;
        fileChipSize.textContent = formatFileSize(file.size);
        fileChip.classList.remove("hidden");
        analyzeBtn.classList.remove("hidden");
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    function showUploadError(msg) {
        uploadError.textContent = msg;
        uploadError.classList.remove("hidden");
    }
    function hideUploadError() {
        uploadError.classList.add("hidden");
    }

    analyzeBtn.addEventListener("click", () => {
        if (selectedFile) handleFileUpload(selectedFile);
    });

    // ============ UPLOAD + ANALYSIS PIPELINE ============
    function handleFileUpload(file) {
        uploadSection.classList.add("hidden");
        errorSection.classList.add("hidden");
        loadingSection.classList.remove("hidden");
        resetLoadingUi();

        const formData = new FormData();
        formData.append("file", file);

        let loadingStep = 0;
        const interval = setInterval(() => {
            loadingStep++;
            if (loadingStep === 1) {
                advanceLoadingStep("parse", "Extracting resume content", "Reading text and detecting sections.");
            } else if (loadingStep === 3) {
                advanceLoadingStep("extract", "Analyzing structure", "Identifying candidate details, skills, and experience.");
            } else if (loadingStep === 6) {
                advanceLoadingStep("analyze", "Evaluating ATS readiness", "Running compatibility and completeness checks.");
            } else if (loadingStep === 8) {
                advanceLoadingStep("report", "Preparing your report", "Putting together the final analysis.");
            }
        }, 1000);

        fetch("/api/analyze", { method: "POST", body: formData })
            .then(response => {
                clearInterval(interval);
                if (!response.ok) {
                    return response.json()
                        .then(err => { throw new Error(err.error || "Analysis failed"); })
                        .catch(() => { throw new Error("Analysis failed"); });
                }
                return response.json();
            })
            .then(data => {
                markAllStepsDone();
                setTimeout(() => {
                    loadingSection.classList.add("hidden");
                    resultsContainer.classList.remove("hidden");
                    newUploadBtn.classList.remove("hidden");
                    downloadPdfBtn.classList.remove("hidden");
                    renderResults(data, file);
                    setupScrollSpy();
                }, 500);
            })
            .catch(err => {
                clearInterval(interval);
                loadingSection.classList.add("hidden");
                showErrorScreen(err.message);
            });
    }

    function resetLoadingUi() {
        Object.values(loadingStepEls).forEach(el => el.dataset.state = "pending");
        loadingStepEls.upload.dataset.state = "done";
        loadingStepEls.parse.dataset.state = "active";
        loadingStatus.textContent = "Analyzing your resume";
        loadingSubtext.textContent = "This usually takes a few seconds.";
    }

    const stepOrder = ["upload", "parse", "extract", "analyze", "report"];
    function advanceLoadingStep(stepKey, title, subtext) {
        const idx = stepOrder.indexOf(stepKey);
        stepOrder.forEach((key, i) => {
            if (i < idx) loadingStepEls[key].dataset.state = "done";
        });
        loadingStepEls[stepKey].dataset.state = "active";
        loadingStatus.textContent = title;
        loadingSubtext.textContent = subtext;
    }

    function markAllStepsDone() {
        Object.values(loadingStepEls).forEach(el => el.dataset.state = "done");
    }

    function showErrorScreen(message) {
        let title = "Something went wrong";
        let friendly = "We couldn't process that file. Please try another PDF or DOCX.";

        if (message) {
            const lower = message.toLowerCase();
            if (lower.includes("extract")) {
                title = "Extraction failed";
                friendly = "We couldn't reliably extract text from this resume. Please try another PDF/DOCX.";
            } else if (lower.includes("ai") || lower.includes("gemini") || lower.includes("llm")) {
                title = "AI analysis unavailable";
                friendly = "Resume text was extracted, but AI analysis is currently unavailable. Please try again shortly.";
            } else if (lower.includes("format") || lower.includes("unsupported") || lower.includes("invalid")) {
                title = "Invalid file";
                friendly = "Please upload a PDF or DOCX file.";
            }
        }

        errorTitle.textContent = title;
        errorMessage.textContent = friendly;
        errorSection.classList.remove("hidden");
    }

    errorRetryBtn.addEventListener("click", () => {
        errorSection.classList.add("hidden");
        uploadSection.classList.remove("hidden");
    });

    // ============ RENDER RESULTS ============
    function renderResults(data, file) {
        currentAnalysisData = data;

        renderReportHeader(data, file);
        renderScore(data);
        renderScoreBreakdown(data.ats_scores);
        renderOverview(data);

        renderList(strengthsAsFindings(data.strengths), "strengths");

        renderCompatibilityTable();
        compatReadiness.textContent = `${data.ats_scores.ats_compatibility} / 15`;

        completenessBar.style.width = `${data.completeness.completeness_percent}%`;
        completenessText.textContent = `${data.completeness.completeness_percent}% complete`;
        renderCompletenessGrid(data.completeness.sections);

        renderSkills();

        const kwIntel = data.keyword_intelligence;
        if (kwIntel && kwIntel.domain_strength) {
            renderKeywords(kwIntel.domain_strength);
        }

        achievementsCount.textContent = `${data.impact_analysis.strong_quantified_bullets} / ${data.impact_analysis.total_relevant_bullets}`;
        renderSimpleList(detectedAchievementsList, data.achievement_report.detected_achievements, "No quantified achievements detected yet.");
        renderSimpleList(actionSuggestionsList, data.achievement_report.suggestions, "No suggestions — bullet formatting looks good.");

        renderExplanations(data.category_explanations);
        renderTopImprovements(data.top_improvements);
        renderDetailedWeaknesses(data.detailed_weaknesses);
        renderSimulation(data.ats_simulation);
        renderQualityDashboard(data);
        renderExtractedProfile(data.canonical_resume);

        rawJsonBlock.textContent = JSON.stringify(data, null, 2);
    }

    function renderReportHeader(data, file) {
        const profile = data.canonical_resume || {};
        const personal = profile.personal_info || {};

        candidateName.textContent = personal.name || "Candidate";

        const contactParts = [personal.email, personal.phone, personal.location].filter(Boolean);
        candidateContact.textContent = contactParts.length > 0 ? contactParts.join(" · ") : "Contact information not detected";

        metaFilename.textContent = file ? file.name : "—";
        metaDate.textContent = new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });

        reportInterpretation.textContent = data.ai_summary || "Analysis complete — see the sections below for a full breakdown.";
    }

    function renderScore(data) {
        const score = data.ats_scores.overall_score;
        scoreDisplay.textContent = score;

        let rating = "Needs Improvement";
        let ratingColor = "var(--color-fail)";
        if (score >= 90) { rating = "Excellent"; ratingColor = "var(--color-pass)"; }
        else if (score >= 80) { rating = "Strong"; ratingColor = "var(--accent-cyan)"; }
        else if (score >= 70) { rating = "Good"; ratingColor = "var(--accent-primary)"; }
        else if (score >= 60) { rating = "Fair"; ratingColor = "var(--color-warn)"; }

        scoreRating.textContent = rating;
        scoreRating.style.color = ratingColor;

        const circumference = 2 * Math.PI * 42; // r=42
        const offset = circumference - (circumference * (score / 100));
        scoreCircleFill.style.strokeDasharray = circumference;
        scoreCircleFill.style.strokeDashoffset = offset;
        scoreCircleFill.style.stroke = ratingColor;
    }

    function renderScoreBreakdown(scores) {
        categoryScoreList.innerHTML = "";
        const categories = [
            { name: "ATS Compatibility", score: scores.ats_compatibility, max: 15 },
            { name: "Resume Structure", score: scores.resume_structure, max: 15 },
            { name: "Keyword / Job Relevance", score: scores.keyword_relevance, max: 20 },
            { name: "Content Quality", score: scores.content_quality, max: 15 },
            { name: "Skills Representation", score: scores.skills_representation, max: 10 },
            { name: "Quantified Impact", score: scores.quantified_impact, max: 10 },
            { name: "Resume Completeness", score: scores.completeness, max: 10 },
            { name: "Readability & Consistency", score: scores.readability_consistency, max: 5 }
        ];

        categories.forEach(c => {
            const pct = (c.score / c.max) * 100;
            const item = document.createElement("div");
            item.className = "category-item";
            item.innerHTML = `
                <div class="category-labels">
                    <span class="category-name">${c.name}</span>
                    <span class="category-points">${c.score}/${c.max}</span>
                </div>
                <div class="progress-bar-track">
                    <div class="progress-bar-fill" style="width: ${pct}%"></div>
                </div>
            `;
            categoryScoreList.appendChild(item);
        });
    }

    function renderOverview(data) {
        const strengths = (data.strengths || []).slice(0, 5);
        const issues = (data.weaknesses || []).slice(0, 5);
        renderSimpleList(overviewStrengths, strengths, "No major strengths detected.");
        renderSimpleList(overviewIssues, issues, "No major issues detected.");

        const topImprovement = (data.top_improvements && data.top_improvements[0]) || null;
        overviewPriority.textContent = topImprovement
            ? topImprovement.title
            : "No priority action identified.";
    }

    function strengthsAsFindings(strengths) {
        return strengths || [];
    }

    function renderList(items, kind) {
        const container = kind === "strengths" ? strengthsList : null;
        if (!container) return;
        container.innerHTML = "";
        if (!items || items.length === 0) {
            container.innerHTML = `<p class="weakness-empty">No strengths detected yet.</p>`;
            return;
        }
        items.forEach(text => {
            const card = document.createElement("div");
            card.className = "finding-card";
            card.innerHTML = `
                <span class="finding-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </span>
                <div class="finding-body"><p>${escapeHtml(text)}</p></div>
            `;
            container.appendChild(card);
        });
    }

    function renderSimpleList(container, list, emptyMsg = "None detected.") {
        container.innerHTML = "";
        if (!list || list.length === 0) {
            const li = document.createElement("li");
            li.textContent = emptyMsg;
            li.style.color = "var(--text-dark)";
            container.appendChild(li);
            return;
        }
        list.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item;
            container.appendChild(li);
        });
    }

    function renderCompatibilityTable() {
        if (!currentAnalysisData) return;
        compatibilityChecksTable.innerHTML = "";

        const checks = currentAnalysisData.ats_compatibility.checks;
        const filtered = checks.filter(c => activeCompatFilter === "all" || c.status === activeCompatFilter);

        if (filtered.length === 0) {
            compatibilityChecksTable.innerHTML = `<tr><td colspan="3" style="text-align:center; color: var(--text-dark); padding: var(--sp-8) 0;">No checks match the active filter.</td></tr>`;
            return;
        }

        filtered.forEach(c => {
            const row = document.createElement("tr");
            const badgeInfo = statusBadge(c.status);
            row.innerHTML = `
                <td data-label="Check"><strong>${escapeHtml(c.name)}</strong></td>
                <td data-label="Status"><span class="status-badge ${badgeInfo.cls}">${badgeInfo.label}</span></td>
                <td data-label="Detail" class="check-message-cell">${escapeHtml(c.message)}</td>
            `;
            compatibilityChecksTable.appendChild(row);
        });
    }

    function statusBadge(rawStatus) {
        const status = String(rawStatus).toLowerCase();
        if (status === "pass") return { cls: "pass", label: "✓ Pass" };
        if (status === "warn" || status === "warning") return { cls: "warn", label: "⚠ Warning" };
        if (status === "fail") return { cls: "fail", label: "✕ Fail" };
        return { cls: "", label: rawStatus };
    }

    function renderCompletenessGrid(sections) {
        completenessSectionsGrid.innerHTML = "";
        for (const [name, detected] of Object.entries(sections)) {
            const item = document.createElement("div");
            item.className = `section-grid-item ${detected ? "detected" : ""}`;
            item.innerHTML = `
                <span class="sec-status-dot" aria-hidden="true"></span>
                <span class="sec-name">${escapeHtml(name)}</span>
                <span class="sec-status-label">${detected ? "Detected" : "Not detected"}</span>
            `;
            completenessSectionsGrid.appendChild(item);
        }
    }

    function renderSkills() {
        if (!currentAnalysisData) return;
        skillsDisplayContainer.innerHTML = "";
        const profile = currentAnalysisData.skill_profile;
        if (!profile) return;

        if (activeSkillTab === "categorized") {
            const cats = profile.categorized_skills;
            if (!cats || Object.keys(cats).length === 0) {
                skillsDisplayContainer.innerHTML = `<p class="weakness-empty">No categorized skills returned.</p>`;
                return;
            }
            for (const [catName, list] of Object.entries(cats)) {
                if (!list || list.length === 0) continue;
                const block = document.createElement("div");
                block.className = "skill-category-block";
                block.innerHTML = `
                    <h5 class="skill-cat-title">${escapeHtml(catName)}</h5>
                    <div class="skill-tag-cloud">${list.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}</div>
                `;
                skillsDisplayContainer.appendChild(block);
            }
        } else {
            const norms = profile.normalized_skills;
            if (!norms || norms.length === 0) {
                skillsDisplayContainer.innerHTML = `<p class="weakness-empty">No normalized skills returned.</p>`;
                return;
            }
            skillsDisplayContainer.innerHTML = `<div class="skill-tag-cloud">${norms.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}</div>`;
        }
    }

    function renderKeywords(keywords) {
        keywordStrengthList.innerHTML = "";
        for (const [domain, strength] of Object.entries(keywords)) {
            const item = document.createElement("div");
            item.className = "keyword-item";
            const strengthClass = String(strength).toLowerCase().replace(/\s+/g, "-");
            item.innerHTML = `
                <span class="kw-name">${escapeHtml(domain)}</span>
                <span class="kw-badge ${strengthClass}">${escapeHtml(strength)}</span>
            `;
            keywordStrengthList.appendChild(item);
        }
    }

    function renderExplanations(exps) {
        const container = document.getElementById("category-explanations-container");
        container.innerHTML = "";
        if (!exps || exps.length === 0) return;

        exps.forEach(e => {
            const div = document.createElement("div");
            div.className = "explanation-item";
            div.innerHTML = `
                <div class="explanation-item-header">
                    <span class="explanation-item-title">${escapeHtml(e.category_name)}</span>
                    <span class="explanation-item-score">${e.score} / ${e.max_score}</span>
                </div>
                <div class="explanation-block">
                    <span class="explanation-block-label">Diagnosis</span>
                    <p>${escapeHtml(e.why)}</p>
                </div>
                ${e.evidence && e.evidence.length > 0 ? `
                <div class="explanation-block">
                    <span class="explanation-block-label">Evidence found</span>
                    <ul class="overview-mini-list">${e.evidence.map(ev => `<li>${escapeHtml(ev)}</li>`).join("")}</ul>
                </div>` : ""}
                ${e.reducing_factors && e.reducing_factors.length > 0 ? `
                <div class="explanation-block">
                    <span class="explanation-block-label">Score-reducing factors</span>
                    <ul class="overview-mini-list">${e.reducing_factors.map(rf => `<li>${escapeHtml(rf)}</li>`).join("")}</ul>
                </div>` : ""}
                <div class="explanation-block">
                    <span class="explanation-block-label">How to improve</span>
                    <p>${escapeHtml(e.improvement_advice)}</p>
                </div>
            `;
            container.appendChild(div);
        });
    }

    function renderTopImprovements(improvements) {
        const container = document.getElementById("top-improvements-list");
        container.innerHTML = "";
        if (!improvements || improvements.length === 0) {
            container.innerHTML = `<p class="weakness-empty">No improvement suggestions available.</p>`;
            return;
        }
        improvements.forEach(imp => {
            const li = document.createElement("li");
            li.innerHTML = `
                <div class="improvement-body">
                    <strong>${escapeHtml(imp.title)}</strong>
                    <span>${escapeHtml(imp.description)}</span>
                </div>
            `;
            container.appendChild(li);
        });
    }

    function renderDetailedWeaknesses(weaks) {
        allWeaknesses = weaks || [];
        filterAndRenderWeaknesses("all");
    }

    function filterAndRenderWeaknesses(severity) {
        const container = document.getElementById("detailed-weaknesses-list-container");
        container.innerHTML = "";
        const filtered = allWeaknesses.filter(w => severity === "all" || w.severity === severity);

        if (filtered.length === 0) {
            container.innerHTML = `<p class="weakness-empty">No weaknesses found for this severity category.</p>`;
            return;
        }

        filtered.forEach(w => {
            const div = document.createElement("div");
            div.className = `weakness-item-card severity-${w.severity}`;
            const showContext = w.context && !["Page Layout Structure", "Document Encoding", "Contact Header"].includes(w.context);
            div.innerHTML = `
                <div class="weakness-header">
                    <span class="weakness-title">${escapeHtml((w.category || "").replace(/_/g, " "))}</span>
                    <span class="weakness-severity-badge ${w.severity}">${escapeHtml(w.severity)}</span>
                </div>
                <p class="weakness-message">${escapeHtml(w.message)}</p>
                ${showContext ? `<div class="weakness-context">${escapeHtml(w.context)}</div>` : ""}
            `;
            container.appendChild(div);
        });
    }

    function renderSimulation(sim) {
        if (!sim) return;
        const badge = document.getElementById("sim-overall-badge");
        const container = document.getElementById("simulation-checks-container");

        const overallInfo = statusBadge(sim.overall_status);
        badge.className = `status-badge ${overallInfo.cls}`;
        badge.textContent = overallInfo.label;

        container.innerHTML = "";
        sim.checks.forEach(c => {
            const row = document.createElement("tr");
            const info = statusBadge(c.status);
            row.innerHTML = `
                <td data-label="Check"><strong>${escapeHtml(c.name)}</strong></td>
                <td data-label="Status"><span class="status-badge ${info.cls}">${info.label}</span></td>
                <td data-label="Detail" class="check-message-cell">${escapeHtml(c.details)}</td>
            `;
            container.appendChild(row);
        });
    }

    // ============ QUALITY DASHBOARD ============
    // No dedicated quality-dashboard data is provided by the API today, so
    // this renders a compact empty state instead of leaving the card blank
    // (which previously stretched to match its sibling's height).
    function renderQualityDashboard(data) {
        const container = document.getElementById("quality-indicators-container");
        if (!container) return;
        container.innerHTML = `<p class="weakness-empty">No additional quality metrics for this report.</p>`;
    }

    // ============ EXTRACTED RESUME PROFILE (collapsible) ============
    function renderExtractedProfile(profile) {
        extractedProfileContainer.innerHTML = "";
        if (!profile) {
            extractedProfileContainer.innerHTML = `<p class="weakness-empty">No extracted profile data available.</p>`;
            return;
        }

        const sections = [
            { key: "personal_info", label: "Personal Information", render: renderPersonalInfoBlock },
            { key: "education", label: "Education", render: renderListEntriesBlock(e => ({
                title: [e.degree, e.field].filter(Boolean).join(", ") || e.institution || "Education entry",
                sub: [e.institution, [e.start_year, e.graduation_year].filter(Boolean).join(" – ")].filter(Boolean).join(" · ")
            })) },
            { key: "experience", label: "Experience", render: renderListEntriesBlock(e => ({
                title: [e.role, e.company].filter(Boolean).join(" at ") || "Experience entry",
                sub: e.duration || ""
            })) },
            { key: "projects", label: "Projects", render: renderListEntriesBlock(e => ({
                title: e.name || "Project",
                sub: (e.technologies || []).join(", ")
            })) },
            { key: "skills", label: "Skills", render: renderSkillsBlock },
            { key: "certifications", label: "Certifications", render: renderListEntriesBlock(e => ({
                title: e.name || "Certification",
                sub: [e.issuer, e.date].filter(Boolean).join(" · ")
            })) },
        ];

        sections.forEach((section, idx) => {
            const data = profile[section.key];
            const item = document.createElement("div");
            item.className = "profile-accordion-item";

            const bodyId = `profile-body-${idx}`;
            item.innerHTML = `
                <button class="profile-accordion-trigger" type="button" aria-expanded="false" aria-controls="${bodyId}">
                    <span>${section.label}</span>
                    <span class="accordion-arrow" aria-hidden="true">▾</span>
                </button>
                <div class="profile-accordion-body" id="${bodyId}"></div>
            `;

            const body = item.querySelector(".profile-accordion-body");
            body.innerHTML = section.render(data);

            const trigger = item.querySelector(".profile-accordion-trigger");
            trigger.addEventListener("click", () => {
                const isOpen = body.classList.toggle("open");
                trigger.setAttribute("aria-expanded", String(isOpen));
            });

            extractedProfileContainer.appendChild(item);
        });
    }

    function renderPersonalInfoBlock(info) {
        if (!info) return `<p class="weakness-empty">Not detected.</p>`;
        const fields = [
            ["Name", info.name], ["Email", info.email], ["Phone", info.phone],
            ["Location", info.location], ["LinkedIn", info.linkedin],
            ["GitHub", info.github], ["Portfolio", info.portfolio]
        ].filter(([, v]) => v);
        if (fields.length === 0) return `<p class="weakness-empty">Not detected.</p>`;
        return fields.map(([label, value]) => `
            <div class="profile-entry">
                <div class="profile-entry-sub">${escapeHtml(label)}</div>
                <div class="profile-entry-title">${escapeHtml(value)}</div>
            </div>
        `).join("");
    }

    function renderListEntriesBlock(mapFn) {
        return function (entries) {
            if (!entries || entries.length === 0) return `<p class="weakness-empty">Not detected.</p>`;
            return entries.map(e => {
                const { title, sub } = mapFn(e);
                return `
                    <div class="profile-entry">
                        <div class="profile-entry-title">${escapeHtml(title)}</div>
                        ${sub ? `<div class="profile-entry-sub">${escapeHtml(sub)}</div>` : ""}
                    </div>
                `;
            }).join("");
        };
    }

    function renderSkillsBlock(skills) {
        if (!skills || skills.length === 0) return `<p class="weakness-empty">Not detected.</p>`;
        return `<div class="skill-tag-cloud">${skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}</div>`;
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    // ============ FILTERS ============
    compatFilters.forEach(btn => {
        btn.addEventListener("click", () => {
            compatFilters.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeCompatFilter = btn.dataset.filter;
            renderCompatibilityTable();
        });
    });

    skillTabFilters.forEach(tab => {
        tab.addEventListener("click", () => {
            skillTabFilters.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeSkillTab = tab.dataset.skillView;
            renderSkills();
        });
    });

    weaknessFilters.forEach(btn => {
        btn.addEventListener("click", () => {
            weaknessFilters.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            filterAndRenderWeaknesses(btn.dataset.weakSeverity);
        });
    });

    // ============ ACCORDIONS ============
    function setupAccordion(btn) {
        if (!btn) return;
        const content = btn.nextElementSibling;
        btn.addEventListener("click", () => {
            const isOpen = content.classList.toggle("open");
            btn.setAttribute("aria-expanded", String(isOpen));
        });
    }
    setupAccordion(jsonAccordionBtn);
    setupAccordion(explanationAccordionBtn);

    // ============ SMOOTH SCROLL NAV ============
    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            const target = document.getElementById(link.dataset.nav);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // ============ PDF DOWNLOAD ============
    downloadPdfBtn.addEventListener("click", () => {
        if (!currentAnalysisData) return;
        window.location.href = `/api/report/pdf?version=${currentAnalysisData.version_id}`;
    });

    // ============ COPY JSON ============
    copyJsonBtn.addEventListener("click", () => {
        if (!currentAnalysisData) return;
        navigator.clipboard.writeText(JSON.stringify(currentAnalysisData, null, 2))
            .then(() => {
                const origText = copyJsonBtn.textContent;
                copyJsonBtn.textContent = "Copied!";
                setTimeout(() => { copyJsonBtn.textContent = origText; }, 2000);
            })
            .catch(err => console.error("Failed to copy:", err));
    });

    // ============ RESET / NEW UPLOAD ============
    function resetToUpload() {
        currentAnalysisData = null;
        selectedFile = null;
        fileInput.value = "";
        fileChip.classList.add("hidden");
        analyzeBtn.classList.add("hidden");
        resultsContainer.classList.add("hidden");
        errorSection.classList.add("hidden");
        newUploadBtn.classList.add("hidden");
        downloadPdfBtn.classList.add("hidden");
        uploadSection.classList.remove("hidden");
        resetLoadingUi();
    }

    resetBtn.addEventListener("click", resetToUpload);
    newUploadBtn.addEventListener("click", resetToUpload);
});
