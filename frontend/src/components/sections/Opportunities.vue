<template>
  <section id="Opportunities">
    <div class="section-header">
      <div>
        <p class="section-eyebrow">Latest listings</p>
        <h2 class="section-title">Browse opportunities</h2>
      </div>
      <a class="section-link" href="#" @click.prevent="resetFilters">Reset filters</a>
    </div>

    <div class="filter-bar">
      <input
        v-model="searchQuery"
        class="search-input"
        type="text"
        placeholder="Search by keyword, topic, department..."
      />

      <select v-model="selectedUni" class="filter-select">
        <option>All universities</option>
        <option v-for="u in uniOptions" :key="u">{{ u }}</option>
      </select>

      <button
        v-for="cat in categories"
        :key="cat"
        @click="activeCat = cat"
        :class="['filter-chip', { active: activeCat === cat }]"
      >
        {{ cat }}
      </button>
    </div>

    <div v-if="loading" style="text-align: center; padding: 40px; color: #888;">
      Loading opportunities...
    </div>

    <div v-else-if="error" style="text-align: center; padding: 40px; color: #c00;">
      Failed to load opportunities. Please try again later.
    </div>

    <div v-else class="cards-grid">
      <div v-for="opp in filteredList" :key="opp.id" class="opp-card">
        <div class="card-top">
          <span :class="['type-tag', opp.tagClass]">{{ opp.typeLabel }}</span>
          <div class="uni-logo-sm">{{ opp.uniShort }}</div>
        </div>

        <div class="card-title">{{ opp.title }}</div>

        <div class="card-meta">
          <div class="card-meta-row">
            <svg viewBox="0 0 24 24"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 3v4M8 3v4"/></svg>
            {{ opp.university }}
          </div>
          <div class="card-meta-row">
            <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
            {{ opp.location }}
          </div>
        </div>

        <div class="card-footer">
          <a class="btn-view" :href="opp.link" target="_blank" rel="noopener">View opportunity</a>
        </div>
      </div>
    </div>

    <div v-if="!loading && !error && filteredList.length === 0" style="text-align: center; padding: 40px; color: #888;">
      No opportunities found matching your criteria.
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const searchQuery = ref('');
const selectedUni = ref('All universities');
const activeCat = ref('All');
const offers = ref([]);
const loading = ref(true);
const error = ref(false);

const categories = ['All', 'Training', 'Thesis', 'Research group', 'Funding partner'];

const TYPE_TAG_CLASS = {
  'training':        'tag-intern',
  'thesis':          'tag-thesis',
  'research_group':  'tag-course',
  'funding_partner': 'tag-job',
};

function mapOffer(o) {
  const typeLower = (o.offer_type ?? '').toLowerCase();
  return {
    id:         o.id,
    title:      o.title,
    university: o.organization?.name ?? '—',
    uniShort:   (o.organization?.name ?? '—').split(' ').map(w => w[0]).join('').slice(0, 4).toUpperCase(),
    typeLabel:  o.offer_type ?? 'Other',
    tagClass:   TYPE_TAG_CLASS[typeLower] ?? 'tag-job',
    category:   o.offer_type ?? 'Other',
    location:   o.country ?? '—',
    link:       o.link ?? '#',
  };
}

onMounted(async () => {
  try {
    const res = await fetch(`${BASE}/api/offers?status=published&page_size=100`);
    if (!res.ok) throw new Error('API error');
    const data = await res.json();
    offers.value = (data.results ?? []).map(mapOffer);
  } catch {
    error.value = true;
  } finally {
    loading.value = false;
  }
});

const uniOptions = computed(() => {
  const names = offers.value.map(o => o.university);
  return [...new Set(names)].sort();
});

const filteredList = computed(() => {
  return offers.value.filter(item => {
    const matchesSearch = !searchQuery.value || item.title.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesUni = selectedUni.value === 'All universities' || item.university === selectedUni.value;
    const matchesCat = activeCat.value === 'All' || item.category.toLowerCase().replace('_', ' ') === activeCat.value.toLowerCase();
    return matchesSearch && matchesUni && matchesCat;
  });
});

const resetFilters = () => {
  searchQuery.value = '';
  selectedUni.value = 'All universities';
  activeCat.value = 'All';
};
</script>
