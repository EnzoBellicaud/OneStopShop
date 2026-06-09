<template>
  <div>
    <AppHeader />

    <section class="page-hero">
      <div class="page-hero-inner">
        <p class="section-eyebrow">Admin</p>
        <h1 class="page-title">Admin Panel</h1>
      </div>
    </section>

    <main class="admin-wrap">
      <!-- Tabs -->
      <div class="admin-tabs">
        <button
          v-for="t in tabs" :key="t.id"
          :class="['admin-tab', { active: activeTab === t.id }]"
          @click="onTabChange(t.id)"
        >{{ t.label }}</button>
      </div>

      <!-- ── TAB: ADD OFFER ── -->
      <section v-if="activeTab === 'add'" class="admin-section">
        <h2 class="section-h2">Add a single opportunity</h2>

        <form class="offer-form" @submit.prevent="submitOffer">
          <div class="form-row-2">
            <label class="field-label">
              Title <span class="req">*</span>
              <input v-model="form.title" class="field-input" placeholder="e.g. Research Fellowship 2025" required />
            </label>
            <label class="field-label">
              Link <span class="req">*</span>
              <input v-model="form.link" class="field-input" type="url" placeholder="https://…" required />
            </label>
          </div>

          <label class="field-label">
            Summary <span class="req">*</span>
            <textarea v-model="form.summary" class="field-input field-textarea" placeholder="Short description of the opportunity" required></textarea>
          </label>

          <div class="form-row-3">
            <label class="field-label">
              Offer type <span class="req">*</span>
              <select v-model="form.offer_type" class="field-input" required>
                <option value="" disabled>Select type</option>
                <option v-for="t in lookups.offerTypes" :key="t.id" :value="t.name">{{ t.name }}</option>
              </select>
            </label>
            <label class="field-label">
              Target profile <span class="req">*</span>
              <select v-model="form.target_profile" class="field-input" required>
                <option value="" disabled>Select profile</option>
                <option v-for="p in lookups.targetProfiles" :key="p.id" :value="p.name">{{ p.name }}</option>
              </select>
            </label>
            <label class="field-label">
              Country <span class="req">*</span>
              <input v-model="form.country" class="field-input" maxlength="2" placeholder="e.g. US" pattern="[A-Za-z]{2}" required style="text-transform:uppercase" />
            </label>
          </div>

          <div class="form-row-3">
            <label class="field-label">
              Organization <span class="req">*</span>
              <select v-model="form.organization_id" class="field-input" required>
                <option value="" disabled>Select organization</option>
                <option v-for="o in lookups.organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
              </select>
            </label>
            <label class="field-label">
              Deadline <span class="field-hint">(optional)</span>
              <input v-model="form.deadline" class="field-input" type="date" />
            </label>
            <label class="field-label">
              Status
              <select v-model="form.status" class="field-input">
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </label>
          </div>

          <div class="field-label">
            <span>Domains <span class="field-hint">(optional)</span></span>
            <div class="domain-grid">
              <label v-for="d in lookups.domains" :key="d.id" class="domain-check">
                <input type="checkbox" :value="d.name" v-model="form.domains" />
                {{ d.name }}
              </label>
            </div>
          </div>

          <div v-if="addError" class="alert-error">{{ addError }}</div>
          <div v-if="addSuccess" class="alert-ok">Offer created successfully.</div>

          <div class="form-actions">
            <button type="submit" class="btn-primary" :disabled="addLoading">
              {{ addLoading ? 'Creating…' : 'Create offer' }}
            </button>
            <button type="button" class="btn-ghost-sm" @click="resetForm">Reset</button>
          </div>
        </form>
      </section>

      <!-- ── TAB: BULK IMPORT ── -->
      <section v-if="activeTab === 'import'" class="admin-section">
        <h2 class="section-h2">Bulk import via Excel</h2>

        <div class="import-help">
          <p>Download the template, fill it in, then upload to preview before confirming.</p>
          <button class="btn-outline" @click="downloadTemplate">Download template (.xlsx)</button>
        </div>

        <div class="upload-area" @dragover.prevent @drop.prevent="onFileDrop">
          <input ref="fileInputRef" type="file" accept=".xlsx,.csv" style="display:none" @change="onFileChange" />
          <div class="upload-box" @click="fileInputRef.click()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
            <span>{{ importFile ? importFile.name : 'Click or drag a file here' }}</span>
          </div>
          <button v-if="importFile" class="btn-primary" :disabled="importLoading" @click="previewImport">
            {{ importLoading ? 'Parsing…' : 'Preview' }}
          </button>
        </div>

        <div v-if="importError" class="alert-error">{{ importError }}</div>

        <!-- Preview results -->
        <template v-if="importPreview">
          <div v-if="importPreview.invalid.length" class="preview-invalid">
            <strong>{{ importPreview.invalid.length }} invalid row(s) skipped:</strong>
            <ul>
              <li v-for="(row, i) in importPreview.invalid" :key="i">
                Row {{ row.row_number ?? i + 2 }}: {{ row.errors?.join(', ') ?? row.error }}
              </li>
            </ul>
          </div>

          <div v-if="importPreview.valid.length" class="preview-valid">
            <div class="preview-header">
              <strong>{{ importPreview.valid.length }} valid row(s)</strong>
              <label class="field-label-inline">
                Default status:
                <select v-model="importDefaultStatus" class="field-input-sm">
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                </select>
              </label>
            </div>

            <div class="table-scroll">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>Title</th><th>Org</th><th>Type</th><th>Profile</th><th>Country</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in importPreview.valid" :key="i">
                    <td>{{ row.data.title || '—' }}</td>
                    <td>{{ row.data.organization }}</td>
                    <td>{{ row.data.offer_type }}</td>
                    <td>{{ row.data.target_profile }}</td>
                    <td>{{ row.data.country }}</td>
                    <td>
                      <select v-model="row.status" class="field-input-sm">
                        <option value="draft">Draft</option>
                        <option value="published">Published</option>
                      </select>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="importResult" class="alert-ok">
              Import complete: {{ importResult.published }} published, {{ importResult.drafts }} drafts.
            </div>

            <div class="form-actions">
              <button class="btn-primary" :disabled="confirmLoading" @click="confirmImport">
                {{ confirmLoading ? 'Importing…' : `Confirm import (${importPreview.valid.length} rows)` }}
              </button>
              <button class="btn-ghost-sm" @click="resetImport">Cancel</button>
            </div>
          </div>

          <div v-if="!importPreview.valid.length && !importPreview.invalid.length" class="alert-error">
            No rows found in the file.
          </div>
        </template>
      </section>

      <!-- ── TAB: MANAGE ── -->
      <section v-if="activeTab === 'manage'" class="admin-section">
        <h2 class="section-h2">Manage opportunities</h2>

        <div class="manage-bar">
          <input v-model="manageQ" class="field-input manage-search" placeholder="Search title, org…" @keyup.enter="loadManageOffers" />
          <select v-model="manageStatus" class="field-input field-input-sm" @change="loadManageOffers">
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <button class="btn-outline" @click="loadManageOffers">Search</button>
        </div>

        <div v-if="manageLoading" class="state-msg">Loading…</div>
        <div v-else-if="manageError" class="alert-error">{{ manageError }}</div>
        <div v-else-if="!manageOffers.length" class="state-msg">No offers found.</div>
        <div v-else>
          <div class="table-scroll">
            <table class="manage-table">
              <thead>
                <tr>
                  <th>Title</th><th>Organization</th><th>Type</th><th>Status</th><th>Created</th><th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="offer in manageOffers" :key="offer.id">
                  <td class="td-title">{{ offer.title }}</td>
                  <td>{{ offer.organization.name }}</td>
                  <td>{{ offer.offer_type }}</td>
                  <td><span :class="['status-pill', `status-${offer.status}`]">{{ offer.status }}</span></td>
                  <td class="td-date">{{ formatDate(offer.created_at) }}</td>
                  <td class="td-actions">
                    <button class="btn-delete" :disabled="deletingId === offer.id" @click="deleteOffer(offer)">
                      {{ deletingId === offer.id ? '…' : 'Delete' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="pagination">
            <button class="page-btn" :disabled="managePage <= 1" @click="changePage(managePage - 1)">← Prev</button>
            <span class="page-info">Page {{ managePage }} / {{ manageTotalPages }}</span>
            <button class="page-btn" :disabled="managePage >= manageTotalPages" @click="changePage(managePage + 1)">Next →</button>
          </div>
        </div>
      </section>

      <!-- ── TAB: ALLOWED DOMAINS ── -->
      <section v-if="activeTab === 'domains'" class="admin-section">
        <h2 class="section-h2">Allowed Teacher Domains</h2>
        <p class="section-desc">Only teachers with an email address from these domains can register. Add institutional domains (e.g. <code>mdu.se</code>) to control who can sign up as a teacher.</p>

        <div v-if="domainsError" class="form-error">{{ domainsError }}</div>
        <div v-if="domainSuccess" class="form-success">{{ domainSuccess }}</div>

        <!-- Add domain form -->
        <div class="domain-add-form">
          <h3 class="sub-h3">Add a new domain</h3>
          <div class="form-row-3">
            <div>
              <label class="field-label">Domain *</label>
              <input v-model="domainForm.domain" class="field-input" placeholder="e.g. mdu.se" />
            </div>
            <div>
              <label class="field-label">University *</label>
              <select v-model="domainForm.organization_id" class="field-input">
                <option value="">Select university…</option>
                <option v-for="org in lookups.organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
              </select>
            </div>
            <div>
              <label class="field-label">Description</label>
              <input v-model="domainForm.description" class="field-input" placeholder="Optional note" />
            </div>
          </div>
          <button class="btn-primary" @click="addDomain" :disabled="domainSaving">
            {{ domainSaving ? 'Adding…' : '+ Add Domain' }}
          </button>
        </div>

        <!-- Domains table -->
        <div v-if="domainsLoading" class="loading-msg">Loading domains…</div>
        <div v-else-if="allowedDomains.length === 0" class="empty-msg">No allowed domains yet. Add one above.</div>
        <div v-else class="table-scroll">
          <table class="manage-table">
            <thead>
              <tr>
                <th>Domain</th>
                <th>University</th>
                <th>Description</th>
                <th>Added</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in allowedDomains" :key="d.id">
                <td><code>{{ d.domain }}</code></td>
                <td>{{ d.organization }}</td>
                <td>{{ d.description || '—' }}</td>
                <td>{{ formatDate(d.created_at) }}</td>
                <td>
                  <button class="btn-danger-sm" @click="deleteDomain(d)">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import { api } from '../services/api.js'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const tabs = [
  { id: 'add',     label: 'Add offer' },
  { id: 'import',  label: 'Bulk import' },
  { id: 'manage',  label: 'Manage offers' },
  { id: 'domains', label: 'Allowed Domains' },
]
const activeTab = ref('add')

// ── Lookups ──
const lookups = reactive({ offerTypes: [], targetProfiles: [], organizations: [], domains: [] })

onMounted(async () => {
  const [ot, tp, orgs, dm] = await Promise.all([
    api.get('/api/lookups/offer-types').then(r => r.json()),
    api.get('/api/lookups/target-profiles').then(r => r.json()),
    api.get('/api/lookups/organizations').then(r => r.json()),
    api.get('/api/lookups/domains').then(r => r.json()),
  ])
  lookups.offerTypes = ot.results ?? []
  lookups.targetProfiles = tp.results ?? []
  lookups.organizations = orgs.results ?? []
  lookups.domains = dm.results ?? []
  loadManageOffers()
})

// ── Add offer ──
const BLANK_FORM = () => ({
  title: '', summary: '', link: '', country: '',
  offer_type: '', organization_id: '', target_profile: '',
  status: 'draft', deadline: '', domains: [],
})
const form = reactive(BLANK_FORM())
const addLoading = ref(false)
const addError = ref('')
const addSuccess = ref(false)

function resetForm() {
  Object.assign(form, BLANK_FORM())
  addError.value = ''
  addSuccess.value = false
}

async function submitOffer() {
  addLoading.value = true
  addError.value = ''
  addSuccess.value = false
  try {
    const res = await api.post('/api/offers', {
      title: form.title,
      summary: form.summary,
      link: form.link,
      country: form.country.toUpperCase(),
      offer_type: form.offer_type,
      organization_id: form.organization_id,
      target_profile: form.target_profile,
      status: form.status,
      deadline: form.deadline || null,
      domains: form.domains,
    })
    if (res.ok) {
      addSuccess.value = true
      resetForm()
      loadManageOffers()
    } else {
      const data = await res.json()
      addError.value = data.detail ?? 'Failed to create offer.'
    }
  } catch {
    addError.value = 'Network error.'
  } finally {
    addLoading.value = false
  }
}

// ── Bulk import ──
const fileInputRef = ref(null)
const importFile = ref(null)
const importLoading = ref(false)
const importError = ref('')
const importPreview = ref(null)
const importDefaultStatus = ref('draft')
const importResult = ref(null)
const confirmLoading = ref(false)

function onFileChange(e) { importFile.value = e.target.files[0] ?? null }
function onFileDrop(e) { importFile.value = e.dataTransfer.files[0] ?? null }

function downloadTemplate() {
  window.open(`${BASE}/api/offers/import/template`, '_blank')
}

async function previewImport() {
  if (!importFile.value) return
  importLoading.value = true
  importError.value = ''
  importPreview.value = null
  importResult.value = null
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await api.upload('/api/offers/import/preview', fd)
    const data = await res.json()
    if (!res.ok) { importError.value = data.error ?? 'Preview failed.'; return }
    // Attach default status to each valid row for per-row control
    data.valid = (data.valid ?? []).map(r => ({ ...r, status: importDefaultStatus.value }))
    importPreview.value = data
  } catch {
    importError.value = 'Network error.'
  } finally {
    importLoading.value = false
  }
}

async function confirmImport() {
  if (!importPreview.value?.valid?.length) return
  confirmLoading.value = true
  importError.value = ''
  try {
    const res = await api.post('/api/offers/import/confirm', { rows: importPreview.value.valid })
    const data = await res.json()
    if (!res.ok) { importError.value = data.error ?? 'Import failed.'; return }
    importResult.value = data
    loadManageOffers()
  } catch {
    importError.value = 'Network error.'
  } finally {
    confirmLoading.value = false
  }
}

function resetImport() {
  importFile.value = null
  importPreview.value = null
  importResult.value = null
  importError.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// ── Manage offers ──
const manageOffers = ref([])
const manageLoading = ref(false)
const manageError = ref('')
const manageQ = ref('')
const manageStatus = ref('')
const managePage = ref(1)
const manageTotalPages = ref(1)
const deletingId = ref(null)
const MANAGE_PAGE_SIZE = 20

async function loadManageOffers() {
  manageLoading.value = true
  manageError.value = ''
  try {
    const params = new URLSearchParams({ page: managePage.value, page_size: MANAGE_PAGE_SIZE })
    if (manageQ.value.trim()) params.set('q', manageQ.value.trim())
    if (manageStatus.value) params.set('status', manageStatus.value)
    const res = await api.get(`/api/offers?${params}`)
    if (!res.ok) { manageError.value = 'Failed to load offers.'; return }
    const data = await res.json()
    manageOffers.value = data.results ?? []
    manageTotalPages.value = data.total_pages ?? 1
  } catch {
    manageError.value = 'Network error.'
  } finally {
    manageLoading.value = false
  }
}

function changePage(p) {
  managePage.value = p
  loadManageOffers()
}

async function deleteOffer(offer) {
  if (!confirm(`Delete "${offer.title}"? This cannot be undone.`)) return
  deletingId.value = offer.id
  try {
    const res = await api.delete(`/api/offers/${offer.id}`)
    if (res.ok || res.status === 204) {
      manageOffers.value = manageOffers.value.filter(o => o.id !== offer.id)
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.detail ?? 'Delete failed.')
    }
  } catch {
    alert('Network error.')
  } finally {
    deletingId.value = null
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

// ── Allowed Domains ──
const allowedDomains = ref([])
const domainsLoading = ref(false)
const domainsError = ref('')
const domainForm = reactive({ domain: '', organization_id: '', description: '' })
const domainSaving = ref(false)
const domainSuccess = ref('')

async function loadAllowedDomains() {
  domainsLoading.value = true
  domainsError.value = ''
  try {
    const res = await api.get('/api/admin/allowed-domains')
    if (!res.ok) { domainsError.value = 'Failed to load domains.'; return }
    const data = await res.json()
    allowedDomains.value = data.results ?? []
  } catch {
    domainsError.value = 'Network error.'
  } finally {
    domainsLoading.value = false
  }
}

async function addDomain() {
  if (!domainForm.domain.trim() || !domainForm.organization_id) {
    domainsError.value = 'Domain and organization are required.'
    return
  }
  domainSaving.value = true
  domainsError.value = ''
  domainSuccess.value = ''
  try {
    const res = await api.post('/api/admin/allowed-domains', {
      domain: domainForm.domain.trim(),
      organization_id: domainForm.organization_id,
      description: domainForm.description.trim(),
    })
    if (res.ok || res.status === 201) {
      domainForm.domain = ''
      domainForm.organization_id = ''
      domainForm.description = ''
      domainSuccess.value = 'Domain added successfully!'
      await loadAllowedDomains()
    } else {
      const data = await res.json().catch(() => ({}))
      domainsError.value = data.message ?? 'Failed to add domain.'
    }
  } catch {
    domainsError.value = 'Network error.'
  } finally {
    domainSaving.value = false
  }
}

async function deleteDomain(domain) {
  if (!confirm(`Remove domain "${domain.domain}"? Teachers with this domain will no longer be able to register.`)) return
  try {
    const res = await api.delete(`/api/admin/allowed-domains/${domain.id}`)
    if (res.ok || res.status === 204) {
      allowedDomains.value = allowedDomains.value.filter(d => d.id !== domain.id)
    } else {
      alert('Failed to delete domain.')
    }
  } catch {
    alert('Network error.')
  }
}

// load domains when tab is clicked
function onTabChange(tabId) {
  activeTab.value = tabId
  if (tabId === 'domains' && allowedDomains.value.length === 0) {
    loadAllowedDomains()
  }
}
</script>

<style scoped>
.admin-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem 3rem 5rem;
}

.admin-tabs {
  display: flex;
  gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 4px;
  margin-bottom: 2rem;
  width: fit-content;
}

.admin-tab {
  padding: 8px 20px;
  border: none;
  border-radius: calc(var(--r) - 2px);
  font-size: 13px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  background: transparent;
  color: var(--ink-soft);
  transition: all 0.15s;
}
.admin-tab.active {
  background: var(--white);
  color: var(--ink);
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

.admin-section { max-width: 800px; }

.section-desc {
  font-size: 0.88rem;
  color: var(--ink-soft);
  margin-bottom: 1.5rem;
  line-height: 1.6;
}
.section-desc code {
  background: #f0f4ff;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.85rem;
}

.domain-add-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.sub-h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 1rem;
}

.form-row-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-success {
  padding: 0.75rem 1rem;
  background: #f0fff4;
  color: #1e6b3a;
  border-radius: var(--r);
  font-size: 0.85rem;
  border-left: 3px solid #22c55e;
  margin-bottom: 1rem;
}

.loading-msg, .empty-msg {
  color: var(--ink-soft);
  font-size: 0.9rem;
  padding: 1rem 0;
}

.btn-danger-sm {
  padding: 4px 10px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #c0392b;
  background: #fde8e8;
  border: 1px solid #f5c2c2;
  border-radius: 4px;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
}
.btn-danger-sm:hover { background: #fbd0d0; }
.section-h2 {
  font-family: 'DM Serif Display', serif;
  font-size: 22px;
  color: var(--ink);
  margin-bottom: 1.5rem;
}

/* Form */
.offer-form { display: flex; flex-direction: column; gap: 16px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 120px; gap: 14px; }

.field-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-soft);
}
.req { color: var(--accent-mid); }
.field-hint { font-weight: 400; color: var(--ink-faint); }

.field-input {
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: var(--ink);
  background: var(--white);
  outline: none;
  transition: border-color 0.15s;
}
.field-input:focus { border-color: var(--ink); }
.field-input-sm { padding: 6px 10px; font-size: 12px; }
.field-textarea { resize: vertical; min-height: 80px; }

.domain-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--white);
  max-height: 160px;
  overflow-y: auto;
}
.domain-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink);
  cursor: pointer;
  font-weight: 400;
}

.form-actions { display: flex; align-items: center; gap: 12px; margin-top: 4px; }
.btn-ghost-sm {
  padding: 9px 18px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: none;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: var(--ink-soft);
  cursor: pointer;
}
.btn-ghost-sm:hover { border-color: var(--ink-soft); }

.btn-outline {
  padding: 9px 18px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--white);
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: var(--ink);
  cursor: pointer;
  font-weight: 500;
}
.btn-outline:hover { border-color: var(--ink); }

.alert-error {
  padding: 10px 14px;
  background: var(--accent-light);
  color: var(--accent-mid);
  border-radius: var(--r);
  font-size: 13px;
}
.alert-ok {
  padding: 10px 14px;
  background: #f0faf4;
  color: #1a6b3c;
  border-radius: var(--r);
  font-size: 13px;
}

/* Import */
.import-help {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 1.5rem;
  font-size: 13px;
  color: var(--ink-soft);
}
.upload-area { display: flex; flex-direction: column; gap: 12px; margin-bottom: 1.5rem; }
.upload-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border: 2px dashed var(--border);
  border-radius: var(--r);
  background: var(--white);
  cursor: pointer;
  font-size: 13px;
  color: var(--ink-soft);
  transition: border-color 0.15s;
}
.upload-box:hover { border-color: var(--ink-soft); }
.upload-box svg { width: 20px; height: 20px; flex-shrink: 0; }

.preview-invalid {
  padding: 12px 16px;
  background: #fff8f0;
  border: 1px solid #f3d5b0;
  border-radius: var(--r);
  font-size: 13px;
  color: #7a3b00;
  margin-bottom: 16px;
}
.preview-invalid ul { margin: 8px 0 0 16px; }
.preview-valid { display: flex; flex-direction: column; gap: 12px; }
.preview-header { display: flex; align-items: center; gap: 16px; font-size: 13px; }
.field-label-inline { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; color: var(--ink-soft); }

.table-scroll { overflow-x: auto; }
.preview-table, .manage-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.preview-table th, .preview-table td,
.manage-table th, .manage-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.preview-table th, .manage-table th {
  font-weight: 600;
  color: var(--ink-soft);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--surface);
}

/* Manage */
.manage-bar { display: flex; gap: 10px; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; }
.manage-search { flex: 1; min-width: 200px; }
.td-title { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-date { white-space: nowrap; color: var(--ink-faint); font-size: 12px; }
.td-actions { white-space: nowrap; }

.status-pill {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 99px;
}
.status-published { background: #f0faf4; color: #1a6b3c; }
.status-draft     { background: var(--surface); color: var(--ink-soft); border: 1px solid var(--border); }
.status-archived  { background: #f5f0ff; color: #5b2da8; }

.btn-delete {
  padding: 5px 12px;
  border: 1px solid #f3d5d5;
  border-radius: var(--r);
  background: #fff8f8;
  color: var(--accent-mid);
  font-size: 12px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-delete:hover { background: var(--accent-light); }
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }

.state-msg { padding: 40px; text-align: center; color: var(--ink-faint); font-size: 14px; }
</style>
