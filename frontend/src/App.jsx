import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;
function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [activePage, setActivePage] = useState("chat");
  const [inventory, setInventory] = useState([]);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryImports, setInventoryImports] = useState([]);
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [inventoryCsv, setInventoryCsv] = useState(null);
  const [importStatus, setImportStatus] = useState("");

  const [newProduct, setNewProduct] = useState({
    product_id: "",
    product_name: "",
    warehouse: "",
    quantity: "",
    reorder_level: "",
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents`);

      console.log("Documents response:", response);

      const data = await response.json();

      console.log("Documents data:", data);

      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Unable to load documents:", error);
    }
  };

  const loadInventory = async () => {
    console.log("Loading inventory...");

    setInventoryLoading(true);

    try {
      const response = await fetch(
       `${API_URL}/inventory`
      );

      const data = await response.json();

      console.log("Inventory received:", data.inventory);

      setInventory(data.inventory || []);
    } catch (error) {
      console.error("Unable to load inventory:", error);
      setInventory([]);
    } finally {
      setInventoryLoading(false);
    }
  };

  const loadInventoryImports = async () => {
    try {
      const response = await fetch(
       `${API_URL}/inventory/imports`
      );

      const data = await response.json();

      setInventoryImports(data.imports || []);
    } catch (error) {
      console.error("Unable to load inventory imports:", error);
    }
  };
  const importInventoryCsv = async () => {
    if (!inventoryCsv) {
      setImportStatus("Please select a CSV file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", inventoryCsv);

    setImportStatus("Importing...");

    try {
      const response = await fetch(
        `${API_URL}/inventory/import`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok || data.error) {
        setImportStatus(data.error || "Import failed.");
        return;
      }

      setImportStatus(
        `✓ ${data.inserted_count} products imported successfully.`
      );

      setInventoryCsv(null);

      await loadInventory();

    } catch (error) {
      console.error("CSV import error:", error);
      setImportStatus("Unable to connect to the backend.");
    }
  };

  const addProduct = async () => {
    if (
      !newProduct.product_id ||
      !newProduct.product_name ||
      !newProduct.warehouse ||
      !newProduct.quantity ||
      !newProduct.reorder_level
    ) {
      alert("Please fill all fields.");
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/inventory/add`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            product_id: newProduct.product_id,
            product_name: newProduct.product_name,
            warehouse: newProduct.warehouse,
            quantity: Number(newProduct.quantity),
            reorder_level: Number(newProduct.reorder_level),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.error || "Unable to add product.");
        return;
      }

      alert("Product added successfully!");

      setNewProduct({
        product_id: "",
        product_name: "",
        warehouse: "",
        quantity: "",
        reorder_level: "",
      });

      setShowAddProduct(false);

      loadInventory();

    } catch (error) {
      alert("Unable to connect to the backend.");
    }
  };

  const deleteDocument = async (filename) => {
    const confirmed = window.confirm(
      `Delete ${filename}?`
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
`${API_URL}/documents/${encodeURIComponent(filename)}`,        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (response.ok) {
        setDocuments((prev) =>
          prev.filter(
            (document) => document.filename !== filename
          )
        );
      } else {
        alert(data.error || "Unable to delete document.");
      }
    } catch (error) {
      alert("Unable to connect to the backend.");
    }
  };

  //jhgfsdfghjkl;

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    setIsListening(true);

    recognition.onresult = (event) => {
      const transcript =
        event.results[0][0].transcript;

      console.log("Voice input:", transcript);

      setQuestion(transcript);
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event.error
      );

      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };
  const sendMessage = async () => {//trdtyuiytresrtyuhtrdesrtyuiydsfguhidzdftyug
    if (!question.trim()) return;

    const userMessage = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
        }),
      });

      const data = await response.json();

      const aiMessage = {
        role: "assistant",
        content: data.answer || data.message || "I couldn't find an answer.",
        sources: data.sources || [],
        rag: data.rag || false,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Unable to connect to the WMS AI Agent.",
        },
      ]);
    }

    setQuestion("");
  };

  const handleKeyDown = (event) => {//hgfxdcgvhbjnkmnbhvgchfgv
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    setSelectedFile(file);
    setUploadStatus("");
  };

  const uploadDocument = async () => {//kjhgfdfghjkl
    if (!selectedFile) {
      setUploadStatus("Please select a PDF or TXT file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setUploadStatus("Uploading...");

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setUploadStatus(data.error || "Upload failed.");
        return;
      }

      setUploadStatus(
        `✓ ${data.filename} uploaded successfully and added to RAG.`
      );

      setSelectedFile(null);
      await loadDocuments();

    } catch (error) {
      setUploadStatus("Unable to connect to the WMS AI Agent.");
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div
            className="logo-icon"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "900",
              fontSize: "22px",
              textShadow: "1px 2px 0px rgba(255, 255, 255, 0.35)",
              boxShadow: "0 4px 0px rgba(80, 50, 130, 0.35), 0 6px 12px rgba(80, 50, 130, 0.18)",
              transform: "translateY(-1px)",
            }}
          >
            ṢṀ
          </div>

          <div>
            <h2
              style={{
                fontWeight: "800",
                textShadow: "2px 2px 0px rgba(255, 255, 255, 0.35), 0 4px 8px rgba(80, 50, 130, 0.18)",
                letterSpacing: "0.5px",
              }}
            >
              StockMind
            </h2>
            <span>Warehouse Intelligence</span>
          </div>
        </div>
        <nav>
          <button
            className={`nav-item ${activePage === "chat" ? "active" : ""
              }`}
            onClick={() => setActivePage("chat")}
          >
            AI Chat
          </button>

          <button
            className={`nav-item ${activePage === "inventory" ? "active" : ""
              }`}
            onClick={() => {
              setActivePage("inventory");
              loadInventory();
              loadInventoryImports();
            }}
          >
            Inventory
          </button>
          <button
            className={`nav-item ${activePage === "documents" ? "active" : ""
              }`}
            onClick={() => {
              setActivePage("documents");
              loadDocuments();
            }}
          >
            Documents
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="status">
            <span className="status-dot"></span>
            System Online
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div>
            <h1>A Smarter Way to Manage Your Stock </h1>
            <p>
              Ask questions about your inventory and warehouse operations.
            </p>
          </div>

          <div className="header-badge">
            <span>●</span> Warehouse Manager <span>●</span>
          </div>
        </header>






        {activePage === "chat" && (//oijhugyftdrsasdftghyjk
          <>
            <section className="chat-container">
              {messages.length === 0 ? (
                <div className="welcome">
                  <div className="welcome-icon">🤖</div>

                  <h2>How can I help?</h2>

                  <p>
                    Ask me about inventory, stock levels, warehouses,
                    or reorder requirements.
                  </p>

                  <div className="suggestions">
                    <button
                      onClick={() =>
                        setQuestion("How many LED Monitors do we have?")
                      }
                    >
                      How many LED Monitors do we have?
                    </button>

                    <button
                      onClick={() =>
                        setQuestion("Which products are running low?")
                      }
                    >
                      Which products are running low?
                    </button>

                    <button
                      onClick={() =>
                        setQuestion("What products are in warehouse W01?")
                      }
                    >
                      What's in warehouse W01?
                    </button>
                  </div>
                </div>
              ) : (
                <div className="messages">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`message ${message.role === "user"
                        ? "user-message"
                        : "ai-message"
                        }`}
                    >
                      <div className="message-avatar">
                        {message.role === "user" ? "You" : "AI"}
                      </div>

                      <div className="message-content">
                        <div>{message.content}</div>

                        {message.rag && message.sources.length > 0 && (
                          <div className="message-sources">
                            <span>📄 Source:</span>{" "}
                            {message.sources.join(", ")}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <div className="input-area">
              <div className="input-wrapper">
                <input
                  type="text"
                  placeholder="Ask about your warehouse..."
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleKeyDown}
                />

                <button
                  className={`voice-button ${isListening ? "listening" : ""}`}
                  onClick={startListening}
                  title="Voice input"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="22" />
                    <line x1="8" y1="22" x2="16" y2="22" />
                  </svg>
                </button>

                <button
                  className="send-button"
                  onClick={sendMessage}
                >
                  ➤
                </button>
              </div>

              <p className="input-note">
                WMS AI can answer questions using your inventory and warehouse
                knowledge.
              </p>
            </div>
          </>
        )}

        {activePage === "documents" && (//kjhgfxdxcgvhbjnk
          <section className="documents-page">
            <div className="documents-card">

              <div className="documents-icon">📄</div>

              <h2>Upload Documents</h2>

              <p>
                Upload warehouse policies, procedures, or other documents.
                WMS AI will process them and make them searchable using RAG.
              </p>

              <label className="file-picker">
                <input
                  type="file"
                  accept=".pdf,.txt,.csv"
                  onChange={handleFileChange}
                />

                <span>Choose PDF, TXT or CSV</span>
              </label>

              {selectedFile && (
                <div className="selected-file">
                  📎 {selectedFile.name}
                </div>
              )}

              <button
                className="upload-button"
                onClick={uploadDocument}
              >
                Upload Document
              </button>

              {uploadStatus && (
                <div className="upload-status">
                  {uploadStatus}
                </div>
              )}

              <div className="documents-list">

                <div className="documents-list-header">
                  <h2>Uploaded Documents</h2>
                  <span>{documents.length} files</span>
                </div>

                {documents.length === 0 ? (
                  <div className="empty-documents">
                    <p>No documents uploaded yet.</p>
                  </div>
                ) : (
                  documents.map((document) => (
                    <div
                      className="document-card"
                      key={document.filename}
                    >

                      <div className="document-info">

                        <div className="document-icon">
                          {document.type === "CSV" ? "📄" : "📄"}
                        </div>

                        <div>
                          <h3>{document.filename}</h3>

                          <span className="document-type">
                            {document.type}
                            {document.type === "CSV"
                              ? " · Structured Data"
                              : " · RAG Document"}
                          </span>
                        </div>

                      </div>

                      <button
                        className="delete-document"
                        onClick={() =>
                          deleteDocument(document.filename)
                        }
                      >
                        Delete
                      </button>

                    </div>
                  ))
                )}

              </div>

            </div>
          </section>
        )}

        {activePage === "inventory" && (
          <section className="inventory-page">
            <div className="inventory-imports-card">

              <div className="inventory-table-header">
                <h3 className="imported-csv-title">Imported CSVs</h3>
                <span>{inventoryImports.length} files</span>
              </div>

              {inventoryImports.length === 0 ? (
                <div className="inventory-empty">
                  No inventory CSVs imported yet.
                </div>
              ) : (

                <div className="csv-table">

                  <div className="csv-table-header">
                    <span>File Name</span>
                    <span>Products</span>
                    <span>Action</span>
                  </div>

                  {inventoryImports.map((file) => (
                    <div
                      className="csv-table-row"
                      key={file.filename}
                    >

                      <span className="csv-file-name">
                        📄 {file.filename}
                      </span>

                      <span>
                        {file.product_count} products
                      </span>

                      <span className="csv-action">

                        <button
                          className="delete-csv-button"
                          onClick={async () => {

                            const confirmed = window.confirm(
                              `Delete ${file.filename} and all ${file.product_count} products imported from it?`
                            );

                            if (!confirmed) return;

                            try {

                              const response = await fetch(
                                `${API_URL}/inventory/import/${encodeURIComponent(
  file.filename
)}`,
                                {
                                  method: "DELETE",
                                }
                              );

                              const data = await response.json();

                              if (!response.ok || data.error) {
                                alert(
                                  data.error ||
                                  "Unable to delete CSV."
                                );
                                return;
                              }

                              await loadInventory();
                              await loadInventoryImports();

                            } catch (error) {

                              alert(
                                "Unable to connect to the backend."
                              );

                            }

                          }}
                        >
                          Delete
                        </button>

                      </span>

                    </div>
                  ))}

                </div>
              )}

            </div>
            <div className="inventory-header">
              <div>
                <h2 className="inventory-overview-title">
                  Inventory Overview
                </h2>
                <p>Current stock levels across your warehouses.</p>
              </div>

              <div className="inventory-actions">

                <button
                  className="add-product-button"
                  onClick={() => setShowAddProduct((prev) => !prev)}
                >
                  {showAddProduct ? "Close" : "+ Add Product"}
                </button>

                <label className="import-csv-button">
                  Import CSV

                  <input
                    type="file"
                    accept=".csv"
                    hidden
                    onChange={(event) => {
                      const file = event.target.files[0];

                      if (file) {
                        setInventoryCsv(file);
                        setImportStatus("");
                      }
                    }}
                  />
                </label>

                <button
                  className="import-confirm-button"
                  onClick={importInventoryCsv}
                  disabled={!inventoryCsv}
                >
                  Upload
                </button>

                <button
                  className="refresh-inventory"
                  onClick={loadInventory}
                >
                  ↻ Refresh
                </button>

              </div>
            </div>

            {inventoryCsv && (
              <div className="csv-selected">
                📄 {inventoryCsv.name}
              </div>
            )}

            {importStatus && (
              <div className="import-status">
                {importStatus}
              </div>
            )}

            {showAddProduct && (
              <div className="add-product-card">
                <h3>Add New Product</h3>

                <div className="product-form">

                  <input
                    type="text"
                    placeholder="Product ID"
                    value={newProduct.product_id}
                    onChange={(e) =>
                      setNewProduct({
                        ...newProduct,
                        product_id: e.target.value,
                      })
                    }
                  />

                  <input
                    type="text"
                    placeholder="Product Name"
                    value={newProduct.product_name}
                    onChange={(e) =>
                      setNewProduct({
                        ...newProduct,
                        product_name: e.target.value,
                      })
                    }
                  />

                  <input
                    type="text"
                    placeholder="Warehouse (e.g. W01)"
                    value={newProduct.warehouse}
                    onChange={(e) =>
                      setNewProduct({
                        ...newProduct,
                        warehouse: e.target.value,
                      })
                    }
                  />

                  <input
                    type="number"
                    placeholder="Quantity"
                    value={newProduct.quantity}
                    onChange={(e) =>
                      setNewProduct({
                        ...newProduct,
                        quantity: e.target.value,
                      })
                    }
                  />

                  <input
                    type="number"
                    placeholder="Reorder Level"
                    value={newProduct.reorder_level}
                    onChange={(e) =>
                      setNewProduct({
                        ...newProduct,
                        reorder_level: e.target.value,
                      })
                    }
                  />

                  <div className="product-form-actions">
                    <button
                      className="cancel-product"
                      onClick={() => setShowAddProduct(false)}
                    >
                      Cancel
                    </button>

                    <button
                      className="save-product"
                      onClick={addProduct}
                    >
                      Add Product
                    </button>
                  </div>

                </div>
              </div>
            )}
            <div className="inventory-stats">
              <div className="inventory-stat-card">
                <span>Total Products</span>
                <strong>{inventory.length}</strong>
              </div>

              <div className="inventory-stat-card">
                <span>Total Units</span>
                <strong>
                  {inventory.reduce(
                    (total, item) => total + item.quantity,
                    0
                  )}
                </strong>
              </div>

              <div className="inventory-stat-card">
                <span>Low Stock</span>
                <strong>
                  {inventory.filter(
                    (item) => item.quantity < item.reorder_level
                  ).length}
                </strong>
              </div>

              <div className="inventory-stat-card">
                <span>Warehouses</span>
                <strong>
                  {new Set(
                    inventory.map((item) => item.warehouse)
                  ).size}
                </strong>
              </div>
            </div>

            <div className="inventory-table-card">
              <div className="inventory-table-header">
                <h3 className="all-inventory-title">
                  All Inventory
                </h3>
                <span>{inventory.length} products</span>
              </div>

              {inventoryLoading ? (
                <div className="inventory-empty">
                  Loading inventory...
                </div>
              ) : inventory.length === 0 ? (
                <div className="inventory-empty">
                  No inventory data available.
                </div>
              ) : (
                <div className="inventory-table-wrapper">
                  <table className="inventory-table">
                    <thead>
                      <tr>
                        <th>Product ID</th>
                        <th>Product</th>
                        <th>Warehouse</th>
                        <th>Quantity</th>
                        <th>Reorder Level</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {inventory.map((item) => {
                        const lowStock =
                          item.quantity < item.reorder_level;

                        return (
                          <tr key={item.product_id}>
                            <td>{item.product_id}</td>

                            <td className="product-name">
                              {item.product_name}
                            </td>

                            <td>{item.warehouse}</td>

                            <td>{item.quantity}</td>

                            <td>{item.reorder_level}</td>

                            <td>
                              <span
                                className={
                                  lowStock
                                    ? "stock-status low"
                                    : "stock-status good"
                                }
                              >
                                {lowStock ? "Low Stock" : "In Stock"}
                              </span>

                              <button
                                className="delete-inventory-button"
                                onClick={async () => {
                                  const confirmed = window.confirm(
                                    `Delete ${item.product_name}?`
                                  );

                                  if (!confirmed) return;

                                  try {
                                    const response = await fetch(
                                     `${API_URL}/inventory/${item.product_id}`,
                                      {
                                        method: "DELETE",
                                      }
                                    );

                                    const data = await response.json();

                                    if (!response.ok || data.error) {
                                      alert(data.error || "Unable to delete product.");
                                      return;
                                    }

                                    await loadInventory();
                                    await loadInventoryImports();

                                  } catch (error) {
                                    alert("Unable to connect to the backend.");
                                  }
                                }}
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;