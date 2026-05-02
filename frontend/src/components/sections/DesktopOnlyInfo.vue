
<!-- THIS APPEARS WHEN YOUR SCREEN IS SMALLER THAN DESKTOP SCREEN -->

<template>
  <div class="desktop-only-overlay">
    <div class="desktop-only-message">
      <h2>This application only works on desktop</h2>
      <p>Enlarge your browser window or open it on your computer.</p>
    </div>
  </div>
</template>

<style scoped>
.desktop-only-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(130deg, #ffad27 0%, #df4a6c 100%); 
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

.desktop-only-message {
  text-align: center;
  max-width: 520px;
  padding: 24px;
}

@media (max-width: 1100px) {
  .desktop-only-overlay {
    display: flex;
  }
}
</style>