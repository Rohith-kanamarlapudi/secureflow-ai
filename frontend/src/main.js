import "./style.css";
import { api } from "./api/client.js";

const app = document.querySelector("#app");

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
}

function errorText(error, fallback) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (detail) {
        return JSON.stringify(detail);
    }

    return error.message || fallback;
}

function clearAuth() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

// ============================================================
// Login
// ============================================================

function renderLogin() {
    app.innerHTML = `
        <div class="login-page">

            <div class="login-card">

                <div class="login-header">
                    <h1>SecureFlow AI</h1>
                    <p>Secure Document Management</p>
                </div>

                <form id="login-form">

                    <div class="form-group">

                        <label for="email">
                            Email
                        </label>

                        <input
                            id="email"
                            type="email"
                            placeholder="admin@secureflow.example.com"
                            value="admin@secureflow.example.com"
                            required
                        />

                    </div>

                    <div class="form-group">

                        <label for="password">
                            Password
                        </label>

                        <input
                            id="password"
                            type="password"
                            placeholder="Enter your password"
                            value="Admin@12345"
                            required
                        />

                    </div>

                    <div
                        id="login-error"
                        class="error-message hidden"
                    ></div>

                    <button
                        id="login-btn"
                        class="login-btn"
                        type="submit"
                    >
                        Login
                    </button>

                </form>

            </div>

        </div>
    `;

    const form =
        document.querySelector("#login-form");

    const button =
        document.querySelector("#login-btn");

    const errorBox =
        document.querySelector("#login-error");

    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            errorBox.classList.add("hidden");

            button.disabled = true;
            button.textContent = "Logging in...";

            try {

                const response =
                    await api.post(
                        "/auth/login",
                        {
                            email:
                                document
                                    .querySelector("#email")
                                    .value
                                    .trim(),

                            password:
                                document
                                    .querySelector("#password")
                                    .value,
                        }
                    );

                const {
                    access_token,
                    refresh_token,
                } = response.data;

                if (!access_token) {
                    throw new Error(
                        "No access token returned by server."
                    );
                }

                localStorage.setItem(
                    "access_token",
                    access_token
                );

                if (refresh_token) {
                    localStorage.setItem(
                        "refresh_token",
                        refresh_token
                    );
                }

                renderDashboard();

            } catch (error) {

                errorBox.textContent =
                    errorText(
                        error,
                        "Unable to connect to backend."
                    );

                errorBox.classList.remove(
                    "hidden"
                );

            } finally {

                button.disabled = false;
                button.textContent = "Login";

            }
        }
    );
}

// ============================================================
// Dashboard
// ============================================================

function renderDashboard() {

    app.innerHTML = `
        <div class="dashboard">

            <header class="dashboard-header">

                <div>

                    <h1>
                        SecureFlow AI
                    </h1>

                    <p>
                        Document Management Dashboard
                    </p>

                </div>

                <button
                    id="logout-btn"
                    class="logout-btn"
                    type="button"
                >
                    Logout
                </button>

            </header>

            <main class="dashboard-main">

                <section class="welcome-section">

                    <h2>
                        Documents
                    </h2>

                    <p>
                        Manage, view and organize
                        your documents securely.
                    </p>

                </section>

                <!-- Upload -->

                <section class="upload-card">

                    <div class="upload-card-header">

                        <div>

                            <h3>
                                Upload Document
                            </h3>

                            <p>
                                Select a document
                                to upload securely.
                            </p>

                        </div>

                    </div>

                    <form
                        id="upload-form"
                        class="upload-form"
                    >

                        <input
                            id="upload-file"
                            type="file"
                            required
                        />

                        <button
                            id="upload-btn"
                            class="upload-btn"
                            type="submit"
                        >
                            Upload
                        </button>

                    </form>

                    <div
                        id="upload-message"
                        class="hidden"
                    ></div>

                </section>

                <!-- Documents -->

                <section class="document-card">

                    <div class="document-card-header">

                        <div>

                            <h3>
                                My Documents
                            </h3>

                            <p id="document-count">
                                Loading documents...
                            </p>

                        </div>

                        <button
                            id="refresh-btn"
                            class="refresh-btn"
                            type="button"
                        >
                            Refresh
                        </button>

                    </div>

                    <div
                        id="error-message"
                        class="error-message hidden"
                    ></div>

                    <div
                        id="loading"
                        class="loading"
                    >
                        Loading documents...
                    </div>

                    <div
                        id="empty-state"
                        class="empty-state hidden"
                    >

                        <h3>
                            No documents found
                        </h3>

                        <p>
                            Upload a document
                            to get started.
                        </p>

                    </div>

                    <div class="table-wrapper">

                        <table
                            id="documents-table"
                            class="documents-table hidden"
                        >

                            <thead>

                                <tr>

                                    <th>
                                        Filename
                                    </th>

                                    <th>
                                        MIME Type
                                    </th>

                                    <th>
                                        Owner
                                    </th>

                                    <th>
                                        Created
                                    </th>

                                    <th>
                                        Status
                                    </th>

                                    <th>
                                        Actions
                                    </th>

                                </tr>

                            </thead>

                            <tbody
                                id="documents-body"
                            ></tbody>

                        </table>

                    </div>

                </section>

                <!-- Version History -->

                <section
                    id="version-history-section"
                    class="version-history-card hidden"
                >

                    <div
                        class="version-history-header"
                    >

                        <div>

                            <h3>
                                Version History
                            </h3>

                            <p
                                id="version-document-name"
                            >
                                Select a document
                            </p>

                        </div>

                        <button
                            id="close-version-history"
                            class="close-btn"
                            type="button"
                        >
                            Close
                        </button>

                    </div>

                    <div
                        id="version-loading"
                        class="loading"
                    >
                        Loading versions...
                    </div>

                    <div
                        id="version-error"
                        class="error-message hidden"
                    ></div>

                    <div
                        id="version-empty"
                        class="empty-state hidden"
                    >

                        <h3>
                            No versions found
                        </h3>

                    </div>

                    <div class="table-wrapper">

                        <table
                            id="versions-table"
                            class="documents-table hidden"
                        >

                            <thead>

                                <tr>

                                    <th>
                                        Version
                                    </th>

                                    <th>
                                        Created
                                    </th>

                                    <th>
                                        SHA-256
                                    </th>

                                    <th>
                                        Signature
                                    </th>

                                    <th>
                                        Integrity
                                    </th>

                                    <th>
                                        Actions
                                    </th>

                                </tr>

                            </thead>

                            <tbody
                                id="versions-body"
                            ></tbody>

                        </table>

                    </div>

                </section>

            </main>

        </div>
    `;

    const documentsBody =
        document.querySelector(
            "#documents-body"
        );

    const documentsTable =
        document.querySelector(
            "#documents-table"
        );

    const loading =
        document.querySelector(
            "#loading"
        );

    const emptyState =
        document.querySelector(
            "#empty-state"
        );

    const errorMessage =
        document.querySelector(
            "#error-message"
        );

    const documentCount =
        document.querySelector(
            "#document-count"
        );

    const uploadForm =
        document.querySelector(
            "#upload-form"
        );

    const uploadFile =
        document.querySelector(
            "#upload-file"
        );

    const uploadButton =
        document.querySelector(
            "#upload-btn"
        );

    const uploadMessage =
        document.querySelector(
            "#upload-message"
        );

    const refreshButton =
        document.querySelector(
            "#refresh-btn"
        );

    const logoutButton =
        document.querySelector(
            "#logout-btn"
        );

    const versionSection =
        document.querySelector(
            "#version-history-section"
        );

    const versionName =
        document.querySelector(
            "#version-document-name"
        );

    const versionLoading =
        document.querySelector(
            "#version-loading"
        );

    const versionError =
        document.querySelector(
            "#version-error"
        );

    const versionEmpty =
        document.querySelector(
            "#version-empty"
        );

    const versionsTable =
        document.querySelector(
            "#versions-table"
        );

    const versionsBody =
        document.querySelector(
            "#versions-body"
        );

    let selectedDocumentId = null;
    let selectedDocumentName = "";

    // ========================================================
    // Load Documents
    // ========================================================

    async function loadDocuments() {

        loading.classList.remove(
            "hidden"
        );

        documentsTable.classList.add(
            "hidden"
        );

        emptyState.classList.add(
            "hidden"
        );

        errorMessage.classList.add(
            "hidden"
        );

        try {

            const response =
                await api.get(
                    "/documents"
                );

            const documents =
                Array.isArray(
                    response.data
                )
                    ? response.data
                    : [];

            documentsBody.innerHTML = "";

            documentCount.textContent =
                `${documents.length} document${
                    documents.length === 1
                        ? ""
                        : "s"
                }`;

            loading.classList.add(
                "hidden"
            );

            if (!documents.length) {

                emptyState.classList.remove(
                    "hidden"
                );

                return;
            }

            documents.forEach(
                (doc) => {

                    const row =
                        document.createElement(
                            "tr"
                        );

                    const createdAt =
                        doc.created_at
                            ? new Date(
                                  doc.created_at
                              ).toLocaleString()
                            : "—";

                    const status =
                        doc.is_archived
                            ? "Archived"
                            : "Active";

                    row.innerHTML = `

                        <td>
                            <strong>
                                ${escapeHtml(
                                    doc.filename ||
                                    "Unnamed"
                                )}
                            </strong>
                        </td>

                        <td>
                            ${escapeHtml(
                                doc.mime_type ||
                                "Unknown"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                doc.owner_id ||
                                "—"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                createdAt
                            )}
                        </td>

                        <td>

                            <span
                                class="status-badge ${
                                    doc.is_archived
                                        ? "archived"
                                        : "active"
                                }"
                            >
                                ${status}
                            </span>

                        </td>

                        <td>

                            <button
                                class="action-btn version-btn"
                                data-document-id="${escapeHtml(
                                    doc.id
                                )}"
                                data-document-name="${escapeHtml(
                                    doc.filename ||
                                    "Unnamed"
                                )}"
                            >
                                Versions
                            </button>

                        </td>
                    `;

                    documentsBody.appendChild(
                        row
                    );
                }
            );

            documentsTable.classList.remove(
                "hidden"
            );

        } catch (error) {

            loading.classList.add(
                "hidden"
            );

            let message =
                errorText(
                    error,
                    "Unable to load documents."
                );

            if (
                error.response?.status === 401
            ) {

                message =
                    "Authentication failed. Please login again.";

                clearAuth();

                errorMessage.textContent =
                    message;

                errorMessage.classList.remove(
                    "hidden"
                );

                setTimeout(
                    renderLogin,
                    500
                );

                return;
            }

            if (
                error.response?.status === 403
            ) {

                message =
                    "You do not have permission to view documents.";

            }

            errorMessage.textContent =
                message;

            errorMessage.classList.remove(
                "hidden"
            );

            documentCount.textContent =
                "Unable to load documents";
        }
    }

    // ========================================================
    // Load Version History
    // ========================================================

    async function loadVersionHistory(
        documentId,
        filename
    ) {

        selectedDocumentId =
            documentId;

        selectedDocumentName =
            filename;

        versionSection.classList.remove(
            "hidden"
        );

        versionName.textContent =
            filename;

        versionLoading.classList.remove(
            "hidden"
        );

        versionError.classList.add(
            "hidden"
        );

        versionEmpty.classList.add(
            "hidden"
        );

        versionsTable.classList.add(
            "hidden"
        );

        versionsBody.innerHTML = "";

        try {

            const response =
                await api.get(
                    `/documents/${documentId}/versions`
                );

            const versions =
                Array.isArray(
                    response.data
                )
                    ? response.data
                    : [];

            versionLoading.classList.add(
                "hidden"
            );

            if (!versions.length) {

                versionEmpty.classList.remove(
                    "hidden"
                );

                return;
            }

            const statuses =
                await Promise.all(
                    versions.map(
                        async (version) => {

                            try {

                                const result =
                                    await api.get(
                                        `/documents/${documentId}/versions/${version.id}/signature`
                                    );

                                return [
                                    version.id,
                                    result.data,
                                ];

                            } catch (error) {

                                if (
                                    error.response?.status ===
                                    404
                                ) {

                                    return [
                                        version.id,
                                        null,
                                    ];
                                }

                                return [
                                    version.id,
                                    {
                                        status:
                                            "ERROR",

                                        error:
                                            errorText(
                                                error,
                                                "Verification failed"
                                            ),
                                    },
                                ];
                            }
                        }
                    )
                );

            const signatureMap =
                Object.fromEntries(
                    statuses
                );

            versions.forEach(
                (version) => {

                    const sig =
                        signatureMap[
                            version.id
                        ];

                    const signatureStatus =
                        sig?.status ||
                        "NOT SIGNED";

                    const modified =
                        sig?.modified ===
                        true;

                    const signatureValid =
                        sig?.signature_valid ===
                        true;

                    const isValid =
                        signatureStatus ===
                        "VALID";

                    const statusClass =
                        isValid
                            ? "valid"
                            : signatureStatus ===
                                "NOT SIGNED"
                            ? "unsigned"
                            : "invalid";

                    const integrityText =
                        sig
                            ? modified
                                ? "Modified"
                                : "Unmodified"
                            : "Not verified";

                    const row =
                        document.createElement(
                            "tr"
                        );

                    row.innerHTML = `

                        <td>
                            <strong>
                                Version
                                ${escapeHtml(
                                    version.version
                                )}
                            </strong>
                        </td>

                        <td>
                            ${escapeHtml(
                                version.created_at
                                    ? new Date(
                                          version.created_at
                                      ).toLocaleString()
                                    : "—"
                            )}
                        </td>

                        <td>

                            <span
                                class="hash-value"
                                title="${escapeHtml(
                                    version.sha256_hash ||
                                    ""
                                )}"
                            >
                                ${escapeHtml(
                                    version.sha256_hash ||
                                    "—"
                                )}
                            </span>

                        </td>

                        <td>

                            <span
                                class="signature-badge ${statusClass}"
                            >
                                ${escapeHtml(
                                    signatureStatus
                                )}
                            </span>

                            ${
                                sig?.signer
                                    ? `
                                        <div
                                            class="signature-detail"
                                        >
                                            Signer:
                                            ${escapeHtml(
                                                sig.signer
                                            )}
                                        </div>
                                    `
                                    : ""
                            }

                            ${
                                sig?.signed_at
                                    ? `
                                        <div
                                            class="signature-detail"
                                        >
                                            Signed:
                                            ${escapeHtml(
                                                new Date(
                                                    sig.signed_at
                                                ).toLocaleString()
                                            )}
                                        </div>
                                    `
                                    : ""
                            }

                        </td>

                        <td>

                            <span
                                class="integrity-text ${
                                    modified
                                        ? "modified"
                                        : isValid
                                        ? "unmodified"
                                        : ""
                                }"
                            >
                                ${escapeHtml(
                                    integrityText
                                )}
                            </span>

                            ${
                                sig
                                    ? `
                                        <div
                                            class="signature-detail"
                                        >
                                            Crypto:
                                            ${
                                                signatureValid
                                                    ? "Valid"
                                                    : "Invalid"
                                            }
                                        </div>
                                    `
                                    : ""
                            }

                        </td>

                        <td
                            class="version-actions"
                        >

                            <button
                                class="action-btn download-version-btn"
                                data-version-id="${escapeHtml(
                                    version.id
                                )}"
                            >
                                Download
                            </button>

                            ${
                                !sig
                                    ? `
                                        <button
                                            class="action-btn sign-version-btn"
                                            data-version-id="${escapeHtml(
                                                version.id
                                            )}"
                                        >
                                            Sign
                                        </button>
                                    `
                                    : ""
                            }

                        </td>
                    `;

                    versionsBody.appendChild(
                        row
                    );
                }
            );

            versionsTable.classList.remove(
                "hidden"
            );

        } catch (error) {

            versionLoading.classList.add(
                "hidden"
            );

            versionError.textContent =
                errorText(
                    error,
                    "Failed to load version history."
                );

            versionError.classList.remove(
                "hidden"
            );
        }
    }

    // ========================================================
    // Download Version
    // ========================================================

    async function downloadVersion(
        versionId,
        button
    ) {

        const originalText =
            button.textContent;

        button.disabled = true;

        button.textContent =
            "Downloading...";

        try {

            const response =
                await api.get(
                    `/documents/${selectedDocumentId}/versions/${versionId}/download`,
                    {
                        responseType:
                            "blob",
                    }
                );

            const url =
                window.URL.createObjectURL(
                    response.data
                );

            const link =
                document.createElement(
                    "a"
                );

            link.href = url;

            const disposition =
                response.headers?.[
                    "content-disposition"
                ];

            const match =
                disposition?.match(
                    /filename="([^"]+)"/
                );

            link.download =
                match?.[1] ||
                `${selectedDocumentName}-version-${versionId}`;

            document.body.appendChild(
                link
            );

            link.click();

            link.remove();

            window.URL.revokeObjectURL(
                url
            );

        } catch (error) {

            alert(
                errorText(
                    error,
                    "Failed to download this version."
                )
            );

        } finally {

            button.disabled = false;

            button.textContent =
                originalText;
        }
    }

    // ========================================================
    // Sign Version
    // ========================================================

    async function signVersion(
        versionId,
        button
    ) {

        button.disabled = true;

        button.textContent =
            "Signing...";

        try {

            await api.post(
                `/documents/${selectedDocumentId}/versions/${versionId}/sign`
            );

            await loadVersionHistory(
                selectedDocumentId,
                selectedDocumentName
            );

        } catch (error) {

            alert(
                errorText(
                    error,
                    "Failed to sign this version."
                )
            );

            button.disabled = false;

            button.textContent =
                "Sign";
        }
    }

    // ========================================================
    // Document Version Button
    // ========================================================

    documentsBody.addEventListener(
        "click",
        (event) => {

            const button =
                event.target.closest(
                    ".version-btn"
                );

            if (!button) {
                return;
            }

            loadVersionHistory(
                button.dataset.documentId,
                button.dataset.documentName
            );
        }
    );

    // ========================================================
    // Version Actions
    // ========================================================

    versionsBody.addEventListener(
        "click",
        (event) => {

            const downloadButton =
                event.target.closest(
                    ".download-version-btn"
                );

            if (downloadButton) {

                downloadVersion(
                    downloadButton.dataset.versionId,
                    downloadButton
                );

                return;
            }

            const signButton =
                event.target.closest(
                    ".sign-version-btn"
                );

            if (signButton) {

                signVersion(
                    signButton.dataset.versionId,
                    signButton
                );
            }
        }
    );

    // ========================================================
    // Close Version History
    // ========================================================

    document
        .querySelector(
            "#close-version-history"
        )
        .addEventListener(
            "click",
            () => {

                versionSection.classList.add(
                    "hidden"
                );

                selectedDocumentId =
                    null;

                selectedDocumentName =
                    "";
            }
        );

    // ========================================================
    // Upload Document
    // ========================================================

    uploadForm.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            const file =
                uploadFile.files[0];

            if (!file) {

                uploadMessage.textContent =
                    "Please select a file.";

                uploadMessage.className =
                    "error-message";

                return;
            }

            uploadButton.disabled = true;

            uploadButton.textContent =
                "Uploading...";

            uploadMessage.className =
                "hidden";

            try {

                const formData =
                    new FormData();

                formData.append(
                    "file",
                    file
                );

                await api.post(
                    "/documents",
                    formData
                );

                uploadMessage.textContent =
                    `Document "${file.name}" uploaded successfully.`;

                uploadMessage.className =
                    "success-message";

                uploadForm.reset();

                await loadDocuments();

            } catch (error) {

                if (
                    error.response?.status ===
                    401
                ) {

                    clearAuth();

                    uploadMessage.textContent =
                        "Authentication failed. Please login again.";

                    uploadMessage.className =
                        "error-message";

                    setTimeout(
                        renderLogin,
                        500
                    );

                    return;
                }

                uploadMessage.textContent =
                    errorText(
                        error,
                        "Failed to upload document."
                    );

                uploadMessage.className =
                    "error-message";

            } finally {

                uploadButton.disabled =
                    false;

                uploadButton.textContent =
                    "Upload";
            }
        }
    );

    // ========================================================
    // Refresh
    // ========================================================

    refreshButton.addEventListener(
        "click",
        loadDocuments
    );

    // ========================================================
    // Logout
    // ========================================================

    logoutButton.addEventListener(
        "click",
        async () => {

            const refreshToken =
                localStorage.getItem(
                    "refresh_token"
                );

            try {

                if (refreshToken) {

                    await api.post(
                        "/auth/logout",
                        null,
                        {
                            params: {
                                token_id:
                                    refreshToken,
                            },
                        }
                    );
                }

            } catch (error) {

                console.error(
                    "Logout request failed:",
                    error
                );
            }

            clearAuth();

            renderLogin();
        }
    );

    // Initial document load

    loadDocuments();
}

// ============================================================
// Application Startup
// ============================================================

async function checkAuthentication() {

    const accessToken =
        localStorage.getItem(
            "access_token"
        );

    if (!accessToken) {

        renderLogin();

        return;
    }

    try {

        await api.get(
            "/documents"
        );

        renderDashboard();

    } catch (error) {

        clearAuth();

        renderLogin();
    }
}

checkAuthentication();