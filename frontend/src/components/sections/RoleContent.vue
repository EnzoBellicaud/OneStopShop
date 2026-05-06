<template>
  <section class="selection-screen" :class="{ 'compact-mode': isSearching }">
    <div class="container">
      <div v-if="!isSearching" class="text-center">
        <h1 class="title">What are you <span>looking for?</span></h1>
        <p class="subtitle">Search opportunities or use quick filters below</p>
      </div>


      <div class="search-wrapper">
        <input 
          type="text" 
          class="search-input" 
          :placeholder="searchPlaceholder || 'Search opportunities...'" 
          @focus="isSearching = true"
        />
      </div>


      <div v-if="!isSearching" class="grid-profiles">
        <div 
          v-for="item in shortcuts" 
          :key="item" 
          class="shortcut-card"
          @click="toggleFilter(item)"
        >
          <span class="item-name">{{ item }}</span>
          <button class="select-btn">Explore</button>
        </div>
      </div>

     
      <div v-else class="results-layout">
        <aside class="side-filters">
          <h3>Filters</h3>
          <div class="filter-group">
            <h4>Offer Type</h4>
            <label v-for="cat in shortcuts" :key="cat" class="checkbox-item">
              <input 
                type="checkbox" 
                :checked="activeFilters.includes(cat)" 
                @change="toggleFilter(cat)"
              >
              {{ cat }}
            </label>
          </div>
          <button class="reset-btn" @click="isSearching = false">Reset All</button>
        </aside>

        <main class="results-grid">
          <div class="results-header">Showing results for selected filters</div>
          <div class="cards-container">
            <div class="opportunity-card">
              <div class="card-tag">Example</div>
              <h3>Matches your selection</h3>
              <p>Tailored content for your role is displayed here.</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  shortcuts: Array,
  searchPlaceholder: String
})

const isSearching = ref(false)
const activeFilters = ref([])

const toggleFilter = (cat) => {
  isSearching.value = true // Переключаем вид
  const index = activeFilters.value.indexOf(cat)
  if (index > -1) {
    activeFilters.value.splice(index, 1)
  } else {
    activeFilters.value.push(cat)
  }
}
</script>

<style scoped>

.selection-screen {
  min-height: 100vh; 
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px; 
  padding-top: 100px;
  background-color: transparent; 
}

.container {
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.text-center {
  text-align: center;
  margin-bottom: 50px;
}

.title {
  font-size: 3.5rem;
  font-weight: 800;
  color: var(--ink, #111);
  margin-bottom: 10px;
}

.title span { color: var(--accent-mid, #d63031); }

.subtitle {
  font-size: 1.2rem;
  color: #666;
}


.search-wrapper {
  position: relative;
  max-width: 800px;
  margin: 0 auto 60px;
}

.search-icon {
  position: absolute;
  left: 25px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  z-index: 2;
}

.search-input {
  width: 100%;
  padding: 20px 30px 20px 70px;
  font-size: 1.2rem;
  border-radius: 24px;
  border: 1px solid #eee;
  background: white;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 10px 15px -3px;
  outline: none;
  transition: all 0.3s ease;
}

.search-input:focus {
  box-shadow: rgba(0, 0, 0, 0.2) 0px 20px 25px -5px;
  border-color: var(--accent-mid, #d63031);
}


.grid-profiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.shortcut-card {
  background: var(--peach, #fff5f0);
  padding: 25px;
  border-radius: 20px;
  border: 1px solid #eee;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 6px;
}

.shortcut-card:hover {
  transform: translateY(-5px);
  box-shadow: rgba(0, 0, 0, 0.15) 0px 10px 20px;
  border-color: var(--ink, #111);
}

.item-name {
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: capitalize;
  color: var(--ink, #111);
}

.select-btn {
  padding: 8px 16px;
  background: var(--ink, #111);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.shortcut-card:hover .select-btn {
  background: var(--accent-mid, #d63031);
}

.grid-profiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
.shortcut-card {
  background: var(--peach, #fff5f0); padding: 25px; border-radius: 20px;
  border: 1px solid #eee; text-align: center; cursor: pointer;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 6px; transition: 0.3s;
}
.shortcut-card:hover { transform: translateY(-5px); border-color: var(--ink, #111); }

.results-layout { display: grid; grid-template-columns: 250px 1fr; gap: 40px; text-align: left; }
.side-filters { background: white; padding: 20px; border-radius: 20px; border: 1px solid #eee; height: fit-content; }
.checkbox-item { display: block; margin-bottom: 12px; cursor: pointer; }
.opportunity-card { 
  background: white; border: 1px solid #eee; padding: 20px; border-radius: 12px; 
  position: relative; margin-top: 20px;
}
.card-tag { position: absolute; top: 20px; right: 20px; background: #000; color: #fff; padding: 4px 8px; font-size: 0.7rem; border-radius: 4px; }

.select-btn {
  padding: 8px 16px; background: var(--ink, #111); color: white;
  border: none; border-radius: 10px; cursor: pointer;
}
.reset-btn { margin-top: 20px; background: none; border: 1px solid #ddd; padding: 5px 10px; border-radius: 8px; cursor: pointer; }
</style>