const form = document.querySelector("#requirement-form");
const requirementInput = document.querySelector("#requirement");
const generateButton = document.querySelector("#generate-button");
const statusText = document.querySelector("#status");
const resultPanel = document.querySelector("#result-panel");
const exportButton = document.querySelector("#export-button");

let latestResult = null;
const summaryElement = document.querySelector(
    "#requirement-summary"
);
const requirementPointsElement = document.querySelector(
    "#requirement-points"
);
const ambiguitiesElement = document.querySelector(
    "#ambiguities"
);
const assumptionsElement = document.querySelector(
    "#assumptions"
);
const testCasesElement = document.querySelector(
    "#test-cases"
);
const caseCountElement = document.querySelector(
    "#case-count"
);
const requirementFileInput = document.querySelector(
    "#requirement-file"
);

const selectedFileName = document.querySelector(
    "#selected-file-name"
);
const historyList = document.querySelector("#history-list");
const historyStatus = document.querySelector("#history-status");
const refreshHistoryButton = document.querySelector(
    "#refresh-history-button"
);

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const requirement = requirementInput.value.trim();

    if (requirement.length < 10) {
        showError("需求内容至少需要10个字符。");
        return;
    }

    setLoading(true);
    resultPanel.hidden = true;

    try {
        const response = await fetch("/api/test-cases", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                requirement: requirement,
            }),
        });

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(
                responseData.detail || "生成测试用例失败"
            );
        }

        latestResult = responseData;
        renderResult(responseData);
        loadHistory();

        resultPanel.hidden = false;
        statusText.textContent = "生成完成";
        statusText.classList.remove("error");

        resultPanel.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});


function renderResult(data) {
    summaryElement.textContent = data.requirement_summary;

    caseCountElement.textContent =
        `${data.test_cases.length} 条测试用例`;

    renderRequirementPoints(data.requirement_points);

    renderTextList(
        ambiguitiesElement,
        data.ambiguities,
        "未发现明显的需求歧义。"
    );

    renderTextList(
        assumptionsElement,
        data.assumptions,
        "生成过程未使用额外假设。"
    );

    renderTestCases(data.test_cases);
}


function renderRequirementPoints(requirementPoints) {
    requirementPointsElement.replaceChildren();

    requirementPoints.forEach((point) => {
        const listItem = document.createElement("li");

        const requirementId = document.createElement("strong");
        requirementId.textContent = point.requirement_id;

        const description = document.createElement("span");
        description.textContent = ` ${point.description}`;

        listItem.append(requirementId, description);
        requirementPointsElement.append(listItem);
    });
}


function renderTextList(container, items, emptyMessage) {
    container.replaceChildren();

    if (items.length === 0) {
        const listItem = document.createElement("li");
        listItem.textContent = emptyMessage;
        container.append(listItem);
        return;
    }

    items.forEach((item) => {
        const listItem = document.createElement("li");
        listItem.textContent = item;
        container.append(listItem);
    });
}


function renderTestCases(testCases) {
    testCasesElement.replaceChildren();

    testCases.forEach((testCase) => {
        const card = createTestCaseCard(testCase);
        testCasesElement.append(card);
    });
}


function createTestCaseCard(testCase) {
    const card = document.createElement("article");
    card.className = "test-case-card";

    const header = document.createElement("div");
    header.className = "test-case-header";

    const titleGroup = document.createElement("div");

    const caseId = document.createElement("span");
    caseId.className = "case-id";
    caseId.textContent = testCase.case_id;

    const title = document.createElement("h4");
    title.textContent = testCase.title;

    titleGroup.append(caseId, title);

    const tags = document.createElement("div");
    tags.className = "case-tags";

    tags.append(
        createTag(testCase.priority, "priority-tag"),
        createTag(testCase.test_type, "type-tag")
    );

    if (testCase.based_on_assumption) {
        tags.append(
            createTag("包含假设", "assumption-tag")
        );
    }

    header.append(titleGroup, tags);

    const relatedRequirements = document.createElement("p");
    relatedRequirements.className = "related-requirements";
    relatedRequirements.textContent =
        `关联需求：${testCase.related_requirement_ids.join("、")}`;

    const preconditionTitle = document.createElement("h5");
    preconditionTitle.textContent = "前置条件";

    const preconditionList = createTextList(
        testCase.preconditions
    );

    const stepsTitle = document.createElement("h5");
    stepsTitle.textContent = "操作步骤";

    const stepsContainer = document.createElement("div");
    stepsContainer.className = "steps";

    testCase.steps.forEach((step) => {
        const stepElement = document.createElement("div");
        stepElement.className = "step";

        const stepNumber = document.createElement("span");
        stepNumber.className = "step-number";
        stepNumber.textContent = step.step_number;

        const stepContent = document.createElement("div");

        const action = document.createElement("p");
        action.textContent = `操作：${step.action}`;

        const expectedResult = document.createElement("p");
        expectedResult.className = "expected-result";
        expectedResult.textContent =
            `预期：${step.expected_result}`;

        stepContent.append(action, expectedResult);
        stepElement.append(stepNumber, stepContent);
        stepsContainer.append(stepElement);
    });

    card.append(
        header,
        relatedRequirements,
        preconditionTitle,
        preconditionList,
        stepsTitle,
        stepsContainer
    );

    return card;
}


function createTag(text, className) {
    const tag = document.createElement("span");
    tag.className = `tag ${className}`;
    tag.textContent = text;

    return tag;
}


function createTextList(items) {
    const list = document.createElement("ul");

    items.forEach((item) => {
        const listItem = document.createElement("li");
        listItem.textContent = item;
        list.append(listItem);
    });

    return list;
}


function setLoading(isLoading) {
    generateButton.disabled = isLoading;

    generateButton.textContent = isLoading
        ? "正在分析，请稍候……"
        : "分析需求并生成测试用例";

    if (isLoading) {
        statusText.textContent = "DeepSeek正在分析需求";
        statusText.classList.remove("error");
    }
}


function showError(message) {
    statusText.textContent = message;
    statusText.classList.add("error");
}
exportButton.addEventListener("click", exportExcel);


async function exportExcel() {
    if (!latestResult) {
        showError("请先生成测试用例");
        return;
    }

    const originalButtonText = exportButton.textContent;

    exportButton.disabled = true;
    exportButton.textContent = "正在导出……";

    try {
        const response = await fetch("/api/export-excel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(latestResult),
        });

        if (!response.ok) {
            const errorData = await response
                .json()
                .catch(() => ({}));

            throw new Error(
                errorData.detail || "导出 Excel 失败"
            );
        }

        const excelBlob = await response.blob();
        const downloadUrl = URL.createObjectURL(excelBlob);

        const downloadLink = document.createElement("a");

        downloadLink.href = downloadUrl;
        downloadLink.download = "testpilot-test-cases.xlsx";

        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();

        URL.revokeObjectURL(downloadUrl);

        statusText.textContent = "Excel 文件已成功下载";

    } catch (error) {
        showError(error.message);

    } finally {
        exportButton.disabled = false;
        exportButton.textContent = originalButtonText;
    }
}
async function loadHistory() {
    refreshHistoryButton.disabled = true;
    historyStatus.hidden = false;
    historyStatus.textContent = "正在读取历史记录……";
    historyList.replaceChildren();

    try {
        const response = await fetch("/api/history");
        const records = await response.json();

        if (!response.ok) {
            throw new Error(
                records.detail || "读取历史记录失败"
            );
        }

        if (records.length === 0) {
            historyStatus.textContent = "暂时没有历史记录";
            return;
        }

        historyStatus.hidden = true;

        records.forEach((record) => {
            const historyItem = createHistoryItem(record);
            historyList.appendChild(historyItem);
        });

    } catch (error) {
        historyStatus.hidden = false;
        historyStatus.textContent = error.message;
        historyStatus.classList.add("error");

    } finally {
        refreshHistoryButton.disabled = false;
    }
}


function createHistoryItem(record) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "history-item";

    const top = document.createElement("div");
    top.className = "history-item-top";

    const title = document.createElement("h3");
    title.className = "history-item-title";
    title.textContent = `记录 #${record.id}`;

    const time = document.createElement("time");
    time.className = "history-item-time";
    time.textContent = new Date(
    record.created_at
).toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    hour12: false,
});

    top.append(title, time);

    const summary = document.createElement("p");
    summary.className = "history-item-summary";
    summary.textContent = record.requirement_summary;

    const meta = document.createElement("div");
    meta.className = "history-item-meta";

    const caseCount = document.createElement("span");
    caseCount.textContent =
        `${record.test_case_count} 条测试用例`;

    const viewText = document.createElement("span");
    viewText.textContent = "点击查看完整结果";

    meta.append(caseCount, viewText);
    button.append(top, summary, meta);

    button.addEventListener("click", () => {
        loadHistoryDetail(record.id);
    });

    return button;
}


async function loadHistoryDetail(historyId) {
    statusText.textContent = "正在读取历史记录……";
    statusText.classList.remove("error");

    try {
        const response = await fetch(
            `/api/history/${historyId}`
        );

        const historyDetail = await response.json();

        if (!response.ok) {
            throw new Error(
                historyDetail.detail || "读取历史记录失败"
            );
        }

        latestResult = historyDetail.result;
        requirementInput.value = historyDetail.requirement;

        renderResult(historyDetail.result);

        resultPanel.hidden = false;
        statusText.textContent = "历史记录加载完成";
        statusText.classList.remove("error");

        resultPanel.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });

    } catch (error) {
        showError(error.message);
    }
}
refreshHistoryButton.addEventListener(
    "click",
    loadHistory
);

loadHistory();
async function handleRequirementFile(event) {
    const selectedFile = event.target.files[0];

    if (!selectedFile) {
        return;
    }

    requirementFileInput.disabled = true;

    selectedFileName.textContent =
        `正在读取：${selectedFile.name}`;

    selectedFileName.classList.remove(
        "success",
        "error"
    );

    statusText.textContent = "正在提取文档内容……";
    statusText.classList.remove("error");

    try {
        const formData = new FormData();

        formData.append(
            "file",
            selectedFile
        );

        const response = await fetch(
            "/api/documents/extract",
            {
                method: "POST",
                body: formData,
            }
        );

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(
                responseData.detail || "文档读取失败"
            );
        }

        requirementInput.value = responseData.text;

        selectedFileName.textContent =
            `${responseData.filename}，已提取 ` +
            `${responseData.character_count} 个字符`;

        selectedFileName.classList.add("success");

        statusText.textContent =
            "文档内容已填入需求输入框";

        statusText.classList.remove("error");

        requirementInput.focus();

    } catch (error) {
        selectedFileName.textContent = error.message;
        selectedFileName.classList.add("error");

        showError(error.message);

    } finally {
        requirementFileInput.disabled = false;

        // 清空选择值，允许再次选择同一个文件
        requirementFileInput.value = "";
    }
}
requirementFileInput.addEventListener(
    "change",
    handleRequirementFile
);