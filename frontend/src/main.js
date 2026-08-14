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

  const loginForm =
    document.querySelector("#login-form");

  const loginButton =
    document.querySelector("#login-btn");

  const loginError =
    document.querySelector("#login-error");


  loginForm.addEventListener(
    "submit",
    async (event) => {
      event.preventDefault();

      loginError.classList.add("hidden");

      const email =
        document.querySelector("#email").value.trim();

      const password =
        document.querySelector("#password").value;


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


        console.log(
          "Login response:",
          response
        );


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


        console.log(
          "Login successful"
        );

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


        console.log(
          "Status:",
          error.response?.status
        );


        console.log(
          "Response:",
          error.response?.data
        );


        console.log(
          "Request URL:",
          error.config?.url
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

          } else if (
            error.response.data
          ) {

            detail =
              JSON.stringify(
                error.response.data
              );

          } else {

            detail =
              `Login failed with status ${error.response.status}`;

          }

        } else if (error.message) {

          detail =
            error.message;

        }


        loginError.textContent =
          detail;

        loginError.classList.remove(
          "hidden"
        );

      } finally {

        loginButton.disabled = false;

        loginButton.textContent =
          "Login";
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
          <h1>SecureFlow AI</h1>

          <p>
            Document Management Dashboard
          </p>
        </div>

        <button
          id="logout-btn"
          class="logout-btn"
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
              Upload a document to get started.
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


  // ==========================================================
  // Load documents
  // ==========================================================

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
        response
      );


      const documents =
        response.data;


      documentsBody.innerHTML =
        "";


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
        (document) => {

          const row =
            document.createElement(
              "tr"
            );


          const createdAt =
            document.created_at
              ? new Date(
                  document.created_at
                ).toLocaleString()
              : "—";


          row.innerHTML = `

            <td>
              <strong>
                ${escapeHtml(
                  document.filename ||
                  "Unnamed"
                )}
              </strong>
            </td>

            <td>
              ${escapeHtml(
                document.mime_type ||
                "Unknown"
              )}
            </td>

            <td>
              ${escapeHtml(
                document.owner_id ||
                "—"
              )}
            </td>

            <td>
              ${createdAt}
            </td>

            <td>

              <span
                class="status-badge"
              >
                ${
                  document.is_archived
                    ? "Archived"
                    : "Active"
                }
              </span>

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
        "Unable to load documents. Please check your authentication and backend server.";


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


        setTimeout(
          () => {
            renderLogin();
          },
          1000
        );


        return;
      }


      if (
        error.response?.status === 403
      ) {

        message =
          "You do not have permission to view documents.";

      }


      if (
        error.response?.status === 500
      ) {

        message =
          "Backend server error. Check the Uvicorn terminal.";

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


  // ==========================================================
  // HTML escaping
  // ==========================================================

  function escapeHtml(value) {

    const div =
      document.createElement(
        "div"
      );

    div.textContent =
      String(value);

    return div.innerHTML;
  }


  // ==========================================================
  // Refresh
  // ==========================================================

  refreshButton.addEventListener(
    "click",
    () => {
      loadDocuments();
    }
  );


  // ==========================================================
  // Logout
  // ==========================================================

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

const accessToken =
  localStorage.getItem(
    "access_token"
  );


if (accessToken) {

  console.log(
    "Existing access token found"
  );

  renderDashboard();

} else {

  console.log(
    "No access token found"
  );

  renderLogin();
}