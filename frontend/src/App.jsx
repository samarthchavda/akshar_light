import { useEffect, useState, useRef } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const TEMPLATE_KEY = 'akhar_selected_template';

const TEMPLATES = [
  {
    id: 'akhar_classic',
    name: 'Akhar Classic',
    description: 'Original Akhar Light paper layout with red ruled structure.',
  },
  {
    id: 'letter_pad',
    name: 'Letter Pad',
    description: 'Blank letter-pad layout for correspondence (Sanjay Chavda).',
  },
];

const BUSINESS_INFO = {
  company_name: 'Sanjay Dharamshibhai Chavda',
  company_tagline: 'ALL TYPE OF ELECTRICAL WORKS',
  company_address: '"KOMAL DEEP" Satya Narayan Nagar MainRoad, Near. BatukMaharaj Guaashala, Gandhigram, Rajkot.',
  company_contact: 'Call. +91 92274 20287, Email. aksharlight@yahoo.in',
  pan_no: 'AGGPC1817R',
};

const parseInvoiceNumber = (value) => {
  const match = String(value || '').trim().match(/^INV-?(\d+)$/i);
  return match ? Number(match[1]) : 0;
};

const nextInvoiceNumber = (invoices = []) => {
  const maxNumber = invoices.reduce((max, invoice) => Math.max(max, parseInvoiceNumber(invoice.number)), 0);
  return `INV${String(maxNumber + 1).padStart(4, '0')}`;
};

const blankForm = (invoices = []) => ({
  number: nextInvoiceNumber(invoices),
  date: new Date().toISOString().slice(0, 10),
  dueDate: '',
  clientName: '',
  clientAddress: '',
  items: [{ id: 1, desc: '', qty: 1, price: 0 }],
  notes: '',
  nextId: 2,
});

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function readJSON(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
  } catch {
    return fallback;
  }
}

// API calls for authentication
async function signupUser(name, email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Signup failed');
  }
  return response.json();
}

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  return response.json();
}

// API calls for invoices
async function saveInvoiceToDb(userEmail, invoiceData) {
  const response = await fetch(`${API_BASE_URL}/api/invoices/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_email: userEmail, invoice_data: invoiceData }),
  });
  if (!response.ok) {
    throw new Error('Failed to save invoice');
  }
  return response.json();
}

async function getInvoicesFromDb(userEmail) {
  const response = await fetch(`${API_BASE_URL}/api/invoices/${encodeURIComponent(userEmail)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch invoices');
  }
  const data = await response.json();
  return data.invoices || [];
}

async function deleteInvoiceFromDb(userEmail, invoiceId) {
  const response = await fetch(`${API_BASE_URL}/api/invoices/${encodeURIComponent(userEmail)}/${invoiceId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete invoice');
  }
  return response.json();
}

async function fetchHtml(payload) {
  const response = await fetch(`${API_BASE_URL}/api/invoice/html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Preview generation failed');
  }
  return response.text();
}

async function fetchTemplateHtmlById(templateId, context) {
  const response = await fetch(`${API_BASE_URL}/api/template/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, context }),
  });
  if (!response.ok) {
    const txt = await response.text();
    throw new Error(txt || 'Template render failed');
  }
  return response.text();
}

function calculateTotals(form) {
  const subtotal = form.items.reduce((sum, item) => sum + (Number(item.qty) || 0) * (Number(item.price) || 0), 0);
  return {
    subtotal,
    grand: subtotal,
  };
}

async function fetchPdf(payload) {
  const response = await fetch(`${API_BASE_URL}/api/invoice/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'PDF generation failed');
  }
  return response.blob();
}

async function formatLetterNotes(payload) {
  const response = await fetch(`${API_BASE_URL}/api/letter/format`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Letter formatting failed');
  }
  return response.json();
}

function triggerFileDownload(blob, filename) {
  const fileUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = fileUrl;
  anchor.download = filename;
  anchor.rel = 'noopener';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  // Some mobile browsers ignore download; opening the blob still enables save/share.
  if (!('download' in HTMLAnchorElement.prototype)) {
    window.open(fileUrl, '_blank', 'noopener,noreferrer');
  }

  setTimeout(() => URL.revokeObjectURL(fileUrl), 1200);
}

export default function App() {
  const [authMode, setAuthMode] = useState('login');
  const [user, setUser] = useState(null);
  const [invoices, setInvoices] = useState([]);
    const [letters, setLetters] = useState([]);
  const [view, setView] = useState('dashboard');
  const [editingId, setEditingId] = useState(null);
  const [previewInvoice, setPreviewInvoice] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewKind, setPreviewKind] = useState('pdf');
  const [previewDevice, setPreviewDevice] = useState('desktop');
  const [toast, setToast] = useState('');
  const [form, setForm] = useState(blankForm());
  const [isRecording, setIsRecording] = useState(false);
  const [isFormattingLetter, setIsFormattingLetter] = useState(false);
  const recognitionRef = useRef(null);
  const [selectedTemplate, setSelectedTemplate] = useState(localStorage.getItem(TEMPLATE_KEY) || TEMPLATES[0].id);

  useEffect(() => {
    if (!previewUrl) return undefined;
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  useEffect(() => {
    if (!user) return;
    // Load invoices from database when user logs in
    getInvoicesFromDb(user)
      .then((saved) => {
        const allInvoices = (saved || []).filter((entry) => (entry.templateId || entry.template_id) !== 'letter_pad');
        const allLetters = (saved || []).filter((entry) => (entry.templateId || entry.template_id) === 'letter_pad');
        setInvoices(allInvoices);
        setLetters(allLetters);
      })
      .catch(console.error);
  }, [user]);

  useEffect(() => {
    localStorage.setItem(TEMPLATE_KEY, selectedTemplate);
  }, [selectedTemplate]);

  const users = {}; // No longer using localStorage for users
  const currentUserName = user ? user.split('@')[0] : ''; // Extract name from email
  const selectedTemplateMeta = TEMPLATES.find((template) => template.id === selectedTemplate) || TEMPLATES[0];
  const totals = calculateTotals(form);

  const startNewInvoice = (templateId = selectedTemplate) => {
    setSelectedTemplate(templateId);
    // default form; letter pad uses notes as description and clientName as recipient
    const base = blankForm(templateId === 'letter_pad' ? letters : invoices);
    if (templateId === 'letter_pad') {
      base.clientName = '';
      base.clientAddress = '';
      base.items = [];
      base.notes = '';
    }
    setForm(base);
    setEditingId(null);
    setView('new');
  };

  const openPreview = async (invoice, kind = 'html') => {
    // special-case letter-pad template rendering via template endpoint
    if (invoice.template_id === 'letter_pad') {
      const context = {
        company_name: BUSINESS_INFO.company_name,
        company_tagline: invoice.company_tagline,
        recipient_name: invoice.customer_name,
        bill_date: invoice.bill_date,
        lines: (invoice.notes || '').split('\n').slice(0, 10),
        thanks_text: 'Thanks,\nSanjay Chavda',
      };
      const html = await fetchTemplateHtmlById('letter_pad', context);
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      setPreviewInvoice(invoice);
      setPreviewUrl(url);
      setPreviewKind('html');
      return;
    }
    const blob = kind === 'pdf' ? await fetchPdf(invoice) : new Blob([await fetchHtml(invoice)], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    setPreviewInvoice(invoice);
    setPreviewUrl(url);
    setPreviewKind(kind);
  };

  const downloadPdf = async (invoice) => {
    try {
      if (invoice.template_id === 'letter_pad' || invoice.templateId === 'letter_pad') {
        // call template/pdf endpoint
        const context = {
          company_name: invoice.company_name || BUSINESS_INFO.company_name,
          company_tagline: invoice.company_tagline || BUSINESS_INFO.company_tagline,
          recipient_name: invoice.customer_name || invoice.clientName,
          bill_date: invoice.bill_date || invoice.date,
          lines: (invoice.notes || '').split('\n'),
          thanks_text: 'આભાર\nસંજય ચવડા',
        };
        const res = await fetch(`${API_BASE_URL}/api/template/pdf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ template_id: 'letter_pad', context }),
        });
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || 'PDF generation failed');
        }
        const blob = await res.blob();
        triggerFileDownload(blob, `letter_${invoice.number || 'letter'}.pdf`);
        setToast('PDF downloaded');
        return;
      }

      const blob = await fetchPdf(invoice);
      triggerFileDownload(blob, `bill_${invoice.number || 'invoice'}.pdf`);
      setToast('PDF downloaded');
    } catch (error) {
      setToast(`PDF download failed: ${error.message || 'Try again'}`);
    }
  };

  const buildInvoice = () => {
    const sub = form.items.reduce((sum, item) => sum + (Number(item.qty) || 0) * (Number(item.price) || 0), 0);
    return {
      ...BUSINESS_INFO,
      customer_name: form.clientName,
      customer_address: form.clientAddress,
      bill_date: form.date,
      bill_no: form.number,
      pan_no: BUSINESS_INFO.pan_no,
      items: form.items.map((item, index) => ({
        no: index + 1,
        description: item.desc,
        qty: Number(item.qty) || 0,
        rate: Number(item.price) || 0,
      })),
      total_words: '',
      notes: form.notes,
      subtotal: sub,
      template_id: selectedTemplate,
    };
  };

  const saveInvoice = async () => {
    const invoice = {
      id: editingId || Date.now(),
      number: form.number,
      date: form.date,
      clientName: form.clientName,
      clientAddress: form.clientAddress,
      items: form.items,
      notes: form.notes,
      grand: selectedTemplate === 'letter_pad' ? 0 : totals.grand,
      templateId: selectedTemplate,
      user,
    };
    
    try {
      // Save to database
      await saveInvoiceToDb(user, invoice);
      
      // Update local state
      if (selectedTemplate === 'letter_pad') {
        const updatedLetters = editingId
          ? letters.map((item) => (item.id === editingId ? invoice : item))
          : [...letters, invoice];
        setLetters(updatedLetters);
      } else {
        const updatedInvoices = editingId
          ? invoices.map((item) => (item.id === editingId ? invoice : item))
          : [...invoices, invoice];
        setInvoices(updatedInvoices);
      }
      
      setEditingId(null);
      setForm(blankForm(selectedTemplate === 'letter_pad' ? letters : invoices));
      setView(selectedTemplate === 'letter_pad' ? 'letters' : 'list');
      setToast(editingId ? 'Invoice updated' : 'Invoice saved');
    } catch (error) {
      setToast('Failed to save: ' + error.message);
    }
  };

  const deleteInvoice = async (id) => {
    try {
      await deleteInvoiceFromDb(user, id);
      setInvoices((prev) => prev.filter((invoice) => invoice.id !== id));
      setToast('Invoice deleted');
    } catch (error) {
      setToast('Failed to delete: ' + error.message);
    }
  };

  const deleteLetter = async (id) => {
    try {
      await deleteInvoiceFromDb(user, id);
      setLetters((prev) => prev.filter((l) => l.id !== id));
      setToast('Letter deleted');
    } catch (error) {
      setToast('Failed to delete: ' + error.message);
    }
  };

  const editInvoice = (invoice) => {
    setEditingId(invoice.id);
    setSelectedTemplate(invoice.templateId || TEMPLATES[0].id);
    setForm({
      number: invoice.number,
      date: invoice.date,
      dueDate: '',
      clientName: invoice.clientName || '',
      clientAddress: invoice.clientAddress || '',
      items: invoice.items?.map((item, index) => ({
        id: index + 1,
        desc: item.desc,
        qty: item.qty,
        price: item.price,
      })) || [{ id: 1, desc: '', qty: 1, price: 0 }],
      notes: invoice.notes || '',
      nextId: (invoice.items?.length || 0) + 1,
    });
    setView('new');
  };

  const editLetter = (letter) => {
    setEditingId(letter.id);
    setSelectedTemplate('letter_pad');
    setForm({
      number: letter.number || nextInvoiceNumber(letters),
      date: letter.date,
      dueDate: '',
      clientName: letter.clientName || '',
      clientAddress: letter.clientAddress || '',
      items: [],
      notes: letter.notes || '',
      nextId: 1,
    });
    setView('new');
  };

  const renderAuth = () => {
    const handleSubmit = async () => {
      const email = document.getElementById('auth-email').value.trim();
      const password = document.getElementById('auth-pass').value;

      if (!email || !password) {
        setToast('Enter email and password');
        return;
      }

      try {
        if (authMode === 'login') {
          // Login via API
          const result = await loginUser(email, password);
          setUser(email);
          setView('dashboard');
        } else {
          // Signup via API
          const name = document.getElementById('auth-name').value.trim() || email.split('@')[0];
          const result = await signupUser(name, email, password);
          setUser(email);
          setInvoices([]);
          setView('dashboard');
        }
      } catch (error) {
        setToast(error.message);
      }
    };

    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="brand">Akhar Light Billing</div>
          <div className="brand-sub">React frontend with Python PDF backend</div>
          <div className="tabs-auth">
            <button className={`tab-auth ${authMode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode('login')}>Login</button>
            <button className={`tab-auth ${authMode === 'signup' ? 'active' : ''}`} onClick={() => setAuthMode('signup')}>Sign Up</button>
          </div>
          {authMode === 'signup' && (
            <div className="field">
              <label>Full Name</label>
              <input id="auth-name" type="text" placeholder="Your name" />
            </div>
          )}
          <div className="field">
            <label>Email</label>
            <input id="auth-email" type="email" placeholder="email@example.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input id="auth-pass" type="password" placeholder="••••••••" />
          </div>
          <button className="btn-primary" onClick={handleSubmit}>{authMode === 'login' ? 'Sign In' : 'Create Account'}</button>
        </div>
      </div>
    );
  };

  const renderDashboard = () => {
    const totalRevenue = invoices.reduce((sum, invoice) => sum + Number(invoice.grand || 0), 0);
    return (
      <div>
        <div className="panel-header">
          <div>
            <div className="panel-title">Dashboard</div>
            <div className="panel-sub">Welcome back, {currentUserName}</div>
          </div>
          <button className="btn-accent" onClick={() => startNewInvoice()}>+ New Invoice</button>
        </div>
        <div className="stats-grid">
          <div className="stat-card"><div className="stat-label">Total Invoices</div><div className="stat-value blue">{invoices.length}</div></div>
          <div className="stat-card"><div className="stat-label">Total Revenue</div><div className="stat-value green">{money(totalRevenue)}</div></div>
          <div className="stat-card"><div className="stat-label">Last Invoice</div><div className="stat-value purple">{invoices[0]?.number || 'None'}</div></div>
        </div>
        <div className="panel-sub" style={{ marginBottom: 14 }}>Recent Invoices</div>
        {invoices.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🧾</div>
            <div className="empty-text">No invoices yet</div>
            <div className="empty-sub">Create your first invoice to get started</div>
          </div>
        ) : (
          <div className="invoice-list">
            {invoices.slice().reverse().slice(0, 5).map((invoice) => (
              <div className="invoice-card" key={invoice.id}>
                <div className="inv-left">
                  <div className="inv-num">{invoice.number}</div>
                  <div className="inv-client">{invoice.clientName || 'No client name'}</div>
                </div>
                <div className="inv-right">
                  <div className="inv-date">{invoice.date}</div>
                  <div className="inv-amount">{money(invoice.grand)}</div>
                  <div className="inv-actions">
                    <button className="icon-btn" onClick={() => openPreview(buildInvoiceFromStored(invoice))}>👁</button>
                    <button className="icon-btn" onClick={() => editInvoice(invoice)}>✏</button>
                    <button className="icon-btn red" onClick={() => deleteInvoice(invoice.id)}>🗑</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const buildInvoiceFromStored = (invoice) => ({
    ...BUSINESS_INFO,
    customer_name: invoice.clientName,
    customer_address: invoice.clientAddress,
    bill_date: invoice.date,
    bill_no: invoice.number,
    pan_no: BUSINESS_INFO.pan_no,
    items: (invoice.items || []).map((item, index) => ({
      no: index + 1,
      description: item.desc,
      qty: Number(item.qty) || 0,
      rate: Number(item.price) || 0,
    })),
    total_words: '',
    notes: invoice.notes || '',
    template_id: invoice.templateId || selectedTemplate,
  });

  const renderTemplates = () => (
    <div>
      <div className="panel-header">
        <div>
          <div className="panel-title">Templates</div>
          <div className="panel-sub">Select template, then fill invoice data.</div>
        </div>
      </div>
      <div className="templates-grid">
        {TEMPLATES.map((template) => (
          <div className={`template-card ${selectedTemplate === template.id ? 'active' : ''}`} key={template.id}>
            <div className="template-title">{template.name}</div>
            <div className="template-sub">{template.description}</div>
            <div className="template-actions">
              <button
                className="btn-secondary"
                onClick={() => setSelectedTemplate(template.id)}
              >
                {selectedTemplate === template.id ? 'Selected' : 'Select'}
              </button>
              <button
                className="btn-accent"
                onClick={() => startNewInvoice(template.id)}
              >
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderList = () => (
    <div>
      <div className="panel-header">
        <div>
          <div className="panel-title">All Invoices</div>
          <div className="panel-sub">Client Name, Invoice ID, Amount with edit/delete actions</div>
        </div>
        <button className="btn-accent" onClick={() => startNewInvoice()}>+ New Invoice</button>
      </div>
      {invoices.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🧾</div>
          <div className="empty-text">No invoices yet</div>
          <div className="empty-sub">Create your first invoice to get started</div>
        </div>
      ) : (
        <div className="invoice-table-wrap">
          <table className="invoice-table-view">
            <thead>
              <tr>
                <th>Invoice ID</th>
                <th>Client Name</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.slice().reverse().map((invoice) => (
                <tr key={invoice.id}>
                  <td className="inv-id-cell" data-label="Invoice ID">{invoice.number}</td>
                  <td data-label="Client Name">{invoice.clientName || 'No client name'}</td>
                  <td data-label="Amount">{money(invoice.grand)}</td>
                  <td data-label="Date">{invoice.date}</td>
                  <td data-label="Actions">
                    <div className="inv-actions">
                      <button className="icon-btn" title="Preview" onClick={() => openPreview(buildInvoiceFromStored(invoice))}>👁</button>
                      <button className="icon-btn" title="Edit" onClick={() => editInvoice(invoice)}>✏</button>
                      <button className="icon-btn" title="Download" onClick={() => downloadPdf(buildInvoiceFromStored(invoice))}>⬇</button>
                      <button className="icon-btn red" title="Delete" onClick={() => deleteInvoice(invoice.id)}>🗑</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderLetters = () => (
    <div>
      <div className="panel-header">
        <div>
          <div className="panel-title">All Letters</div>
          <div className="panel-sub">Saved letter pads (separate from invoices)</div>
        </div>
        <button className="btn-accent" onClick={() => startNewInvoice('letter_pad')}>+ New Letter</button>
      </div>
      {letters.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✉</div>
          <div className="empty-text">No letters yet</div>
          <div className="empty-sub">Create your first letter to get started</div>
        </div>
      ) : (
        <div className="invoice-table-wrap">
          <table className="invoice-table-view">
            <thead>
              <tr>
                <th>Letter ID</th>
                <th>Recipient</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {letters.slice().reverse().map((letter) => (
                <tr key={letter.id}>
                  <td className="inv-id-cell" data-label="Letter ID">{letter.number}</td>
                  <td data-label="Recipient">{letter.clientName || 'No recipient'}</td>
                  <td data-label="Date">{letter.date}</td>
                  <td data-label="Actions">
                    <div className="inv-actions">
                      <button className="icon-btn" title="Preview" onClick={() => openPreview(buildInvoiceFromStored(letter))}>👁</button>
                      <button className="icon-btn" title="Edit" onClick={() => editLetter(letter)}>✏</button>
                      <button className="icon-btn" title="Download" onClick={() => downloadPdf(buildInvoiceFromStored(letter))}>⬇</button>
                      <button className="icon-btn red" title="Delete" onClick={() => deleteLetter(letter.id)}>🗑</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderBuilder = () => {
    if (selectedTemplate === 'letter_pad') {
      const handlePreview = async () => {
        const payload = {
          ...BUSINESS_INFO,
          customer_name: form.clientName,
          bill_date: form.date,
          notes: form.notes,
          template_id: 'letter_pad',
        };
        await openPreview(payload, 'html');
      };

      const handleAiFormat = async () => {
        if (!form.notes.trim()) {
          setToast('Pehla letter text lakho');
          return;
        }

        try {
          setIsFormattingLetter(true);
          const result = await formatLetterNotes({
            text: form.notes,
            recipient_name: form.clientName,
            bill_date: form.date,
          });

          if (result?.formatted_text?.trim()) {
            setForm((prev) => ({ ...prev, notes: result.formatted_text }));
            setToast(['openai', 'gemini'].includes(result.provider) ? 'AI format applied' : 'Smart format applied');
          } else {
            setToast('No formatting suggestion generated');
          }
        } catch (error) {
          setToast(`Format failed: ${error.message || 'Try again'}`);
        } finally {
          setIsFormattingLetter(false);
        }
      };

      const handleVoiceToggle = () => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
          alert('Speech recognition not supported in this browser');
          return;
        }

        if (isRecording) {
          try { recognitionRef.current && recognitionRef.current.stop(); } catch (e) { /* ignore */ }
          setIsRecording(false);
          return;
        }

        const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognitionRef.current = new Rec();
        recognitionRef.current.lang = 'gu-IN';
        recognitionRef.current.interimResults = false;
        recognitionRef.current.maxAlternatives = 1;
        recognitionRef.current.onresult = (ev) => {
          const text = Array.from(ev.results).map(r => r[0].transcript).join(' ');
          setForm(prev => ({ ...prev, notes: (prev.notes ? prev.notes + '\n' : '') + text }));
        };
        recognitionRef.current.onerror = (err) => {
          console.error('Speech recognition error', err);
          alert('Speech recognition error: ' + (err.error || 'unknown'));
          setIsRecording(false);
        };
        recognitionRef.current.onend = () => {
          setIsRecording(false);
          // auto-preview after capture
          handlePreview();
        };
        setIsRecording(true);
        recognitionRef.current.start();
      };

      return (
        <div>
          <div className="panel-header">
            <div>
              <div className="panel-title">Letter Pad</div>
              <div className="panel-sub">Edit recipient, date and description then preview.</div>
            </div>
            <button className="btn-secondary" onClick={() => setView('templates')}>Change Template</button>
          </div>

          <div className="builder">
            <div className="builder-section">
              <div className="form-row-3">
                <div className="form-group">
                  <label>Recipient</label>
                  <input value={form.clientName} onChange={(e) => setForm((prev) => ({ ...prev, clientName: e.target.value }))} placeholder="Recipient name" />
                </div>
                <div className="form-group">
                  <label>Date</label>
                  <input type="date" value={form.date} onChange={(e) => setForm((prev) => ({ ...prev, date: e.target.value }))} />
                </div>
                <div className="form-group">&nbsp;</div>
              </div>
            </div>

            <div className="builder-section">
              <div className="builder-section-title">Description / Lines</div>
              <div className="form-group">
                <textarea rows={10} value={form.notes} onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))} placeholder="Write the letter body or separate lines with newlines." />
              </div>
            </div>

            <div className="builder-actions">
              <button className="btn-secondary" onClick={() => setView('dashboard')}>← Cancel</button>
              <button className="btn-accent" onClick={handleVoiceToggle}>{isRecording ? '● Recording...' : '🎤 Voice'}</button>
              <button className="btn-accent" style={{ background: 'var(--accent2)' }} onClick={handleAiFormat} disabled={isFormattingLetter}>{isFormattingLetter ? 'AI Formatting...' : '✨ AI Format'}</button>
              <button className="btn-accent" onClick={handlePreview}>👁 Preview</button>
              <button className="btn-accent" onClick={() => saveInvoice()}>{editingId ? '💾 Update' : '💾 Save'}</button>
            </div>
          </div>
        </div>
      );
    }
    const updateItem = (index, key, value) => {
      setForm((prev) => {
        const items = prev.items.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item);
        return { ...prev, items };
      });
    };

    return (
      <div>
        <div className="panel-header">
          <div>
            <div className="panel-title">{editingId ? 'Edit Invoice' : 'New Invoice'}</div>
            <div className="panel-sub">Template: {selectedTemplateMeta.name}</div>
          </div>
          <button className="btn-secondary" onClick={() => setView('templates')}>Change Template</button>
        </div>

        <div className="builder">
          <div className="builder-section">
            <div className="builder-section-title">Invoice Details</div>
            <div className="form-row-3">
              <div className="form-group">
                <label>Invoice Number</label>
                <input value={form.number} onChange={(e) => setForm((prev) => ({ ...prev, number: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>Invoice Date</label>
                <input type="date" value={form.date} onChange={(e) => setForm((prev) => ({ ...prev, date: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>Due Date</label>
                <input type="date" value={form.dueDate} onChange={(e) => setForm((prev) => ({ ...prev, dueDate: e.target.value }))} />
              </div>
            </div>
          </div>

          <div className="builder-section">
            <div className="builder-section-title">Parties</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--muted)', marginBottom: 10 }}>Bill To (Client)</div>
              <div className="form-row">
                <div className="form-group"><label>Client Name</label><input value={form.clientName} onChange={(e) => setForm((prev) => ({ ...prev, clientName: e.target.value }))} /></div>
                <div className="form-group"><label>Address</label><input value={form.clientAddress} onChange={(e) => setForm((prev) => ({ ...prev, clientAddress: e.target.value }))} /></div>
              </div>
          </div>

          <div className="builder-section">
            <div className="builder-section-title">Items</div>
            <table className="items-table">
              <thead>
                <tr>
                  <th>Description</th>
                  <th style={{ width: 90 }}>Qty</th>
                  <th style={{ width: 120 }}>Price</th>
                  <th style={{ width: 120 }}>Total</th>
                  <th style={{ width: 50 }} />
                </tr>
              </thead>
              <tbody>
                {form.items.map((item, index) => {
                  const total = (Number(item.qty) || 0) * (Number(item.price) || 0);
                  return (
                    <tr key={item.id}>
                      <td><input value={item.desc} onChange={(e) => updateItem(index, 'desc', e.target.value)} placeholder="Item description" /></td>
                      <td><input type="number" min="0" value={item.qty} onChange={(e) => updateItem(index, 'qty', e.target.value)} style={{ textAlign: 'center' }} /></td>
                      <td><input type="number" min="0" value={item.price} onChange={(e) => updateItem(index, 'price', e.target.value)} step="0.01" /></td>
                      <td className="item-total">{money(total)}</td>
                      <td><button className="btn-remove" onClick={() => setForm((prev) => prev.items.length > 1 ? { ...prev, items: prev.items.filter((_, itemIndex) => itemIndex !== index) } : prev)}>×</button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <button className="btn-add-row" onClick={() => setForm((prev) => ({ ...prev, items: [...prev.items, { id: prev.nextId, desc: '', qty: 1, price: 0 }], nextId: prev.nextId + 1 }))}>+ Add Item</button>
          </div>

          <div className="builder-section">
            <div className="builder-section-title">Pricing</div>
            <div className="totals-box">
              <div className="total-row"><span className="label">Subtotal</span><span>{money(totals.subtotal)}</span></div>
              <div className="total-row divider grand"><span>Grand Total</span><span>{money(totals.grand)}</span></div>
            </div>
          </div>

          <div className="builder-section">
            <div className="builder-section-title">Notes (Optional)</div>
            <div className="form-group">
              <textarea rows="3" value={form.notes} onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))} placeholder="Payment terms, thank you message, etc." />
            </div>
          </div>

          <div className="builder-actions">
            <button className="btn-secondary" onClick={() => setView('dashboard')}>← Cancel</button>
            <button className="btn-accent" onClick={saveInvoice}>{editingId ? '💾 Update Invoice' : '💾 Save Invoice'}</button>
            <button className="btn-accent" style={{ background: 'var(--success)' }} onClick={() => openPreview(buildInvoice(), 'html')}>👁 Preview</button>
          </div>
        </div>
      </div>
    );
  };

  const onLogout = () => {
    setUser(null);
    setInvoices([]);
    setLetters([]);
    setView('dashboard');
  };

  if (!user) return renderAuth();

  return (
    <div className="main-screen">
      <div className="topbar">
        <div className="topbar-brand">Akhar Light Billing</div>
        <div className="topbar-right">
          <div className="user-badge">Logged in as <span>{currentUserName}</span></div>
          <button className="btn-sm btn-danger-sm" onClick={onLogout}>↩ Logout</button>
        </div>
      </div>

      <div className="content">
        <div className="sidebar">
          <div className="nav-section">Menu</div>
          <button className={`nav-item ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}><span className="nav-icon">⊞</span>Dashboard</button>
          <button className={`nav-item ${view === 'templates' ? 'active' : ''}`} onClick={() => setView('templates')}><span className="nav-icon">◧</span>Templates</button>
          <button className={`nav-item ${view === 'new' ? 'active' : ''}`} onClick={() => startNewInvoice()}><span className="nav-icon">✚</span>New Invoice</button>
          <button className={`nav-item ${view === 'list' ? 'active' : ''}`} onClick={() => setView('list')}><span className="nav-icon">◩</span>All Invoices</button>
          <button className={`nav-item ${view === 'letters' ? 'active' : ''}`} onClick={() => setView('letters')}><span className="nav-icon">✉</span>Letters</button>
        </div>

        <div className="panel">
          {view === 'dashboard' && renderDashboard()}
          {view === 'templates' && renderTemplates()}
          {view === 'new' && renderBuilder()}
          {view === 'list' && renderList()}
          {view === 'letters' && renderLetters()}
        </div>
      </div>

      {previewInvoice && previewUrl && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) { setPreviewInvoice(null); setPreviewUrl(''); } }}>
          <div className="modal" style={{ width: 'min(95vw, 980px)', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header">
              <div className="modal-title">Invoice {previewInvoice.number} Preview</div>
              <button className="modal-close" onClick={() => { setPreviewInvoice(null); setPreviewUrl(''); }}>×</button>
            </div>
            
            <div className="device-selector" style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button 
                className={`device-btn ${previewDevice === 'mobile' ? 'active' : ''}`}
                onClick={() => setPreviewDevice('mobile')}
                style={{ 
                  padding: '6px 12px', 
                  fontSize: '12px', 
                  borderRadius: '6px', 
                  border: previewDevice === 'mobile' ? '2px solid var(--accent)' : '1px solid var(--border2)',
                  background: previewDevice === 'mobile' ? 'var(--accent)' : 'transparent',
                  color: previewDevice === 'mobile' ? '#fff' : 'var(--muted)',
                  cursor: 'pointer'
                }}
              >📱 Mobile</button>
              <button 
                className={`device-btn ${previewDevice === 'tablet' ? 'active' : ''}`}
                onClick={() => setPreviewDevice('tablet')}
                style={{ 
                  padding: '6px 12px', 
                  fontSize: '12px', 
                  borderRadius: '6px', 
                  border: previewDevice === 'tablet' ? '2px solid var(--accent)' : '1px solid var(--border2)',
                  background: previewDevice === 'tablet' ? 'var(--accent)' : 'transparent',
                  color: previewDevice === 'tablet' ? '#fff' : 'var(--muted)',
                  cursor: 'pointer'
                }}
              >📑 Tablet</button>
              <button 
                className={`device-btn ${previewDevice === 'desktop' ? 'active' : ''}`}
                onClick={() => setPreviewDevice('desktop')}
                style={{ 
                  padding: '6px 12px', 
                  fontSize: '12px', 
                  borderRadius: '6px', 
                  border: previewDevice === 'desktop' ? '2px solid var(--accent)' : '1px solid var(--border2)',
                  background: previewDevice === 'desktop' ? 'var(--accent)' : 'transparent',
                  color: previewDevice === 'desktop' ? '#fff' : 'var(--muted)',
                  cursor: 'pointer'
                }}
              >💻 Desktop</button>
            </div>

            <div className="modal-body" style={{ flex: 1, overflow: 'auto', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '20px', background: '#1a1d25', position: 'relative' }}>
              <div className="pdf-actions-mobile">
                <button className="pdf-action-btn close-btn" onClick={() => { setPreviewInvoice(null); setPreviewUrl(''); setView('list'); }} title="Close and go to invoices">✕</button>
                <button className="pdf-action-btn download-btn" onClick={() => downloadPdf(buildInvoiceFromStored(previewInvoice))} title="Download PDF">⬇</button>
              </div>
              <div className={`device-frame device-${previewDevice}`}>
                <iframe title={`Invoice ${previewKind} Preview`} src={previewUrl} className="pdf-frame" style={{ width: '100%', height: '100%', border: 'none' }} />
              </div>
            </div>

            <div className="modal-footer" style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', display: 'flex', gap: '10px', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <button className="btn-secondary" onClick={() => { setPreviewInvoice(null); setPreviewUrl(''); setView('list'); }}>← Close & Go to Invoices</button>
              <button className="btn-accent" style={{ background: 'var(--success)', flex: 1, minWidth: '150px', fontWeight: 600, padding: '10px 16px' }} onClick={() => downloadPdf(buildInvoiceFromStored(previewInvoice))}>⬇ Download PDF</button>
            </div>
          </div>
        </div>
      )}

      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  );
}
