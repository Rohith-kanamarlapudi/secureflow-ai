import "./style.css";
import { api } from "./api/client.js";

const app = document.querySelector("#app");

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
                        <label for="email">Email</label>

                        <input
                            id="email"
                            type="email"
                            placeholder="admin@secureflow.example.com"
                            value="admin@secureflow.example.com"
                            required
                        />
                    </div>

                    <div class="form-group">
                        <label for="password">Password</label>

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
                        type="submit"
                        class="login-btn"
                    >
                        Login
                    </button>

                </form>

            </div>
        </div>
    `;

    const loginForm = document.querySelector("#login-form");
    const loginButton = document.querySelector("#login-btn");
    const loginError = document.querySelector("#login-error");

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        loginError.classList.add("hidden");

        const email = document
            .querySelector("#email")
            .value
            .trim();

        const password = document
            .querySelector("#password")
            .value;

        loginButton.disabled = true;
        loginButton.textContent = "Logging in...";

        try {
            console.log("Attempting login...");
            console.log("Email:", email);

            const response = await api.post(
                "/auth/login",
                {
                    email,
                    password,
                }
            );

            console.log("Login response:", response.data);

            const {
                access_token,
                refresh_token,
            } = response.data;

            if (!access_token) {
                throw new Error(
                    "No access token returned by server"
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

            console.log("Login successful");

            console.log(
                "Access token stored:",
                Boolean(
                    localStorage.getItem(
                        "access_token"
                    )
                )
            );

            renderDashboard();

        } catch (error) {
            console.error(
                "LOGIN ERROR:",
                error
            );

            let detail =
                "Unable to connect to backend.";

            if (error.response) {
                if (
                    typeof error.response.data?.detail ===
                    "string"
                ) {
                    detail =
                        error.response.data.detail;

                } else if (error.response.data) {
                    detail =
                        JSON.stringify(
                            error.response.data
                        );

                } else {
                    detail =
                        `Login failed with status ${error.response.status}`;
                }

            } else if (error.message) {
                detail = error.message;
            }

            loginError.textContent = detail;

            loginError.classList.remove(
                "hidden"
            );

        } finally {
            loginButton.disabled = false;
            loginButton.textContent = "Login";
        }
    });
}

// ============================================================
// Dashboard
// ============================================================

function renderDashboard() {
    app.innerHTML = `
        <div class="dashboard">

            <header class="dashboard-header">

                <div>
                    <h1>SecureFlow AI</h1>
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

                    <h2>Documents</h2>

                    <p>
                        Manage, view and organize
                        your documents securely.
                    </p>

                </section>

                <!-- Upload -->

                <section class="upload-card">

                    <div class="upload-card-header">

                        <div>
                            <h3>Upload Document</h3>

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
                            type="submit"
                            class="upload-btn"
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
                            <h3>My Documents</h3>

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

                        <h3>No documents found</h3>

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
                                    <th>Filename</th>
                                    <th>MIME Type</th>
                                    <th>Owner</th>
                                    <th>Created</th>
                                    <th>Status</th>
                                </tr>
                            </thead>

                            <tbody
                                id="documents-body"
                            ></tbody>

                        </table>

                    </div>

                </section>

            </main>

        </div>
    `;

    // ========================================================
    // DOM references
    // ========================================================

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

    const refreshButton =
        document.querySelector(
            "#refresh-btn"
        );

    const logoutButton =
        document.querySelector(
            "#logout-btn"
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

    // ========================================================
    // Load documents
    // ========================================================

    async function loadDocuments() {
        loading.classList.remove("hidden");

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
            console.log(
                "Loading documents..."
            );

            const token =
                localStorage.getItem(
                    "access_token"
                );

            console.log(
                "Access token exists:",
                Boolean(token)
            );

            const response =
                await api.get(
                    "/documents"
                );

            console.log(
                "Documents response:",
                response.data
            );

            const documents =
                response.data;

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

            // IMPORTANT:
            // Use "doc" instead of "document"
            // so we don't shadow window.document.

            documents.forEach((doc) => {
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
                        <span class="status-badge">
                            ${
                                doc.is_archived
                                    ? "Archived"
                                    : "Active"
                            }
                        </span>
                    </td>
                `;

                documentsBody.appendChild(
                    row
                );
            });

            documentsTable.classList.remove(
                "hidden"
            );

        } catch (error) {
            console.error(
                "FAILED TO LOAD DOCUMENTS:",
                error
            );

            console.log(
                "Status:",
                error.response?.status
            );

            console.log(
                "Response:",
                error.response?.data
            );

            loading.classList.add(
                "hidden"
            );

            let message =
                "Unable to load documents.";

            // 401 = invalid/expired token

            if (
                error.response?.status === 401
            ) {
                message =
                    "Authentication failed. Please login again.";

                localStorage.removeItem(
                    "access_token"
                );

                localStorage.removeItem(
                    "refresh_token"
                );

                errorMessage.textContent =
                    message;

                errorMessage.classList.remove(
                    "hidden"
                );

                setTimeout(() => {
                    renderLogin();
                }, 500);

                return;
            }

            // 403 = permission problem

            if (
                error.response?.status === 403
            ) {
                message =
                    "You do not have permission to view documents.";
            }

            // 500 = backend problem

            if (
                error.response?.status === 500
            ) {
                message =
                    "Backend server error. Check the Uvicorn terminal.";
            }

            // Network error

            if (!error.response) {
                message =
                    "Unable to connect to the backend server.";
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
    // Upload document
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

            uploadMessage.textContent =
                "";

            uploadMessage.className =
                "hidden";

            try {
                console.log(
                    "Uploading document:",
                    file.name
                );

                const formData =
                    new FormData();

                formData.append(
                    "file",
                    file
                );

                console.log(
                    "FormData contains file:",
                    formData.has("file")
                );

                /*
                 * IMPORTANT:
                 *
                 * Do NOT manually set:
                 *
                 * Content-Type: multipart/form-data
                 *
                 * Axios/browser automatically creates
                 * the multipart boundary.
                 */

                const response =
                    await api.post(
                        "/documents",
                        formData
                    );

                console.log(
                    "Upload response:",
                    response.data
                );

                uploadMessage.textContent =
                    `Document "${file.name}" uploaded successfully.`;

                uploadMessage.className =
                    "success-message";

                uploadForm.reset();

                // Reload list after upload
                await loadDocuments();

            } catch (error) {
                console.error(
                    "UPLOAD FAILED:",
                    error
                );

                console.log(
                    "Upload status:",
                    error.response?.status
                );

                console.log(
                    "Upload response:",
                    error.response?.data
                );

                let message =
                    "Failed to upload document.";

                if (
                    error.response?.status === 401
                ) {
                    message =
                        "Authentication failed. Please login again.";

                    localStorage.removeItem(
                        "access_token"
                    );

                    localStorage.removeItem(
                        "refresh_token"
                    );

                    uploadMessage.textContent =
                        message;

                    uploadMessage.className =
                        "error-message";

                    setTimeout(() => {
                        renderLogin();
                    }, 500);

                    return;
                }

                if (
                    error.response?.status === 403
                ) {
                    message =
                        "You do not have permission to upload documents.";
                }

                if (
                    error.response?.status === 422
                ) {
                    const detail =
                        error.response.data?.detail;

                    message =
                        typeof detail === "string"
                            ? detail
                            : detail
                                ? JSON.stringify(
                                      detail
                                  )
                                : "Invalid upload request.";
                }

                if (
                    error.response?.status === 500
                ) {
                    message =
                        "Backend server error while uploading the document.";
                }

                if (
                    error.response?.data?.detail
                ) {
                    const detail =
                        error.response.data.detail;

                    message =
                        typeof detail === "string"
                            ? detail
                            : JSON.stringify(
                                  detail
                              );
                }

                uploadMessage.textContent =
                    message;

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
    // HTML escaping
    // ========================================================

    function escapeHtml(value) {
        const div =
            document.createElement(
                "div"
            );

        div.textContent =
            String(value);

        return div.innerHTML;
    }

    // ========================================================
    // Refresh
    // ========================================================

    refreshButton.addEventListener(
        "click",
        () => {
            loadDocuments();
        }
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

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "refresh_token"
            );

            renderLogin();
        }
    );

    // Initial document load
    loadDocuments();
}

// ============================================================
// Application startup
// ============================================================

async function checkAuthentication() {
    const accessToken =
        localStorage.getItem(
            "access_token"
        );

    // No token -> Login

    if (!accessToken) {
        console.log(
            "No access token found."
        );

        renderLogin();

        return;
    }

    // Token exists -> verify it with backend

    console.log(
        "Access token found. Validating..."
    );

    try {
        await api.get(
            "/documents"
        );

        console.log(
            "Access token is valid."
        );

        renderDashboard();

    } catch (error) {
        console.error(
            "Authentication check failed:",
            error
        );

        localStorage.removeItem(
            "access_token"
        );

        localStorage.removeItem(
            "refresh_token"
        );

        renderLogin();
    }
}

// Start application
checkAuthentication();