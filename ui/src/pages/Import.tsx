import { useEffect, useState, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Fund } from "../types";

type ImportType = "funds" | "properties" | "balancesheet";

interface ImportOption {
  type: ImportType;
  label: string;
  icon: string;
  description: string;
  columns: string;
}

const IMPORT_OPTIONS: ImportOption[] = [
  {
    type: "funds",
    label: "Funds",
    icon: "\u2637",
    description: "Import fund definitions and fund-property mappings",
    columns: "hMy, sCode, sName, hProperty",
  },
  {
    type: "properties",
    label: "Properties",
    icon: "\u2302",
    description: "Import property records with address and type data",
    columns: "HMY, SCODE, SADDR1, SADDR2, SCITY, SSTATE, SZIPCODE, ITYPE",
  },
  {
    type: "balancesheet",
    label: "Balance Sheet",
    icon: "\u2261",
    description: "Import GL totals for a specific fund's balance sheet",
    columns: "hAccount, sAccountCode, sAccountName, sBegin, sMTD, newTotal, sAccountType",
  },
];

export default function Import() {
  const { currentOrg } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);

  const [selectedType, setSelectedType] = useState<ImportType | null>(null);
  const [funds, setFunds] = useState<Fund[]>([]);
  const [fundsLoading, setFundsLoading] = useState(false);
  const [selectedFundId, setSelectedFundId] = useState("");
  const [sCode, setSCode] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    if (!currentOrg || selectedType !== "balancesheet") return;
    setFundsLoading(true);
    api.get(`/orgs/${currentOrg.id}/funds`)
      .then((res) => setFunds(res.data))
      .catch(() => setFunds([]))
      .finally(() => setFundsLoading(false));
  }, [currentOrg, selectedType]);

  const handleFundChange = (fundId: string) => {
    setSelectedFundId(fundId);
    const fund = funds.find((f) => f.id === fundId);
    setSCode(fund?.sCode || "");
  };

  const handleSelect = (type: ImportType) => {
    setSelectedType(type);
    setFile(null);
    setResult(null);
    setSelectedFundId("");
    setSCode("");
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !currentOrg || !selectedType) return;

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("type", selectedType);
    formData.append("orgId", currentOrg.id);
    formData.append("file", file);

    if (selectedType === "balancesheet") {
      formData.append("fundId", selectedFundId);
      formData.append("sCode", sCode);
    }

    try {
      const res = await api.post("/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult({ ok: true, message: res.data.detail || "Import successful" });
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: any) {
      setResult({
        ok: false,
        message: err.response?.data?.detail || "Import failed",
      });
    } finally {
      setUploading(false);
    }
  };

  if (!currentOrg) return <p>No organization selected.</p>;

  const isAdmin = currentOrg.role === "admin";
  if (!isAdmin) {
    return (
      <div className="import-page">
        <h2>Import Data</h2>
        <div className="import-card">
          <p className="import-restricted">Only administrators can import data.</p>
        </div>
      </div>
    );
  }

  const activeOption = IMPORT_OPTIONS.find((o) => o.type === selectedType);

  return (
    <div className="import-page page-container">
      <h2 className="page-title">Import Data</h2>
      <p className="page-subtitle">
        Upload CSV files to import data into <strong>{currentOrg.name}</strong>
      </p>

      {/* Import type cards */}
      <div className="import-types">
        {IMPORT_OPTIONS.map((opt) => (
          <button
            key={opt.type}
            className={`import-type-card ${selectedType === opt.type ? "import-type-active" : ""}`}
            onClick={() => handleSelect(opt.type)}
          >
            <span className="import-type-icon">{opt.icon}</span>
            <span className="import-type-label">{opt.label}</span>
            <span className="import-type-desc">{opt.description}</span>
          </button>
        ))}
      </div>

      {/* Upload form */}
      {selectedType && activeOption && (
        <div className="import-card">
          <div className="import-card-header">
            <h3>Import {activeOption.label}</h3>
            <span className="import-card-org">{currentOrg.name}</span>
          </div>

          <form onSubmit={handleSubmit} className="import-form">
            {/* Balance sheet extra fields */}
            {selectedType === "balancesheet" && (
              <div className="import-bs-fields">
                <div className="import-field">
                  <label>Fund</label>
                  <div className="select-wrapper">
                    <select
                      className="app-select"
                      value={selectedFundId}
                      onChange={(e) => handleFundChange(e.target.value)}
                      disabled={fundsLoading}
                      required
                    >
                      <option value="">
                        {fundsLoading ? "Loading funds..." : "Select a fund"}
                      </option>
                      {funds.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.sCode} - {f.fundName}
                        </option>
                      ))}
                    </select>
                    {fundsLoading && <span className="select-spinner" />}
                  </div>
                </div>

                <div className="import-field">
                  <label>sCode</label>
                  <input
                    type="text"
                    className="import-input"
                    value={sCode}
                    readOnly
                    placeholder="Auto-filled from fund"
                  />
                </div>
              </div>
            )}

            {/* File upload */}
            <div className="import-field">
              <label>CSV File</label>
              <label className="import-dropzone">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  onChange={(e) => {
                    setFile(e.target.files?.[0] || null);
                    setResult(null);
                  }}
                  required
                />
                {file ? (
                  <div className="import-dropzone-file">
                    <span className="import-dropzone-filename">{file.name}</span>
                    <span className="import-dropzone-size">{(file.size / 1024).toFixed(1)} KB</span>
                  </div>
                ) : (
                  <div className="import-dropzone-placeholder">
                    <span className="import-dropzone-icon">&#8613;</span>
                    <span>Click to select a CSV file</span>
                  </div>
                )}
              </label>
            </div>

            {/* Column hint */}
            <div className="import-hint">
              <span className="import-hint-label">Expected columns:</span>
              <code>{activeOption.columns}</code>
            </div>

            {/* Result */}
            {result && (
              <div className={`import-result ${result.ok ? "import-result-ok" : "import-result-err"}`}>
                {result.ok ? "\u2713" : "\u2717"} {result.message}
              </div>
            )}

            {/* Submit */}
            <div className="import-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setSelectedType(null);
                  setFile(null);
                  setResult(null);
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={uploading || !file}
              >
                {uploading ? "Importing..." : `Import ${activeOption.label}`}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
