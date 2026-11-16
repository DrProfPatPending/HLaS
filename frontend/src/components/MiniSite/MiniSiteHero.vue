<template>
  <section class="mini-site-hero" :class="{ 'has-image': imageUrl }">
    <img
      v-if="imageUrl"
      :key="imageUrl"
      :src="imageUrl"
      alt=""
      class="hero-image"
      @error="onImageError"
    />
    <div v-if="imageUrl" class="hero-overlay" />
    <div class="hero-content">
      <h1 class="hero-title">{{ title }}</h1>
      <p v-if="subtitle" class="hero-subtitle">{{ subtitle }}</p>
    </div>
  </section>
</template>

<script>
export default {
  name: 'MiniSiteHero',
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, default: '' },
    image: { type: String, default: '' },
    fallbackImage: { type: String, default: '' },
  },
  data() {
    return { failedImages: [] };
  },
  computed: {
    candidates() {
      return [...new Set([this.image.trim(), this.fallbackImage.trim()].filter(Boolean))];
    },
    imageUrl() {
      return this.candidates.find(url => !this.failedImages.includes(url)) || '';
    },
  },
  watch: {
    candidates() {
      this.failedImages = [];
    },
  },
  methods: {
    onImageError(event) {
      console.warn('Mini-site hero image failed to load; using the configured fallback.');
      this.failedImages.push(event.target.getAttribute('src'));
    },
  },
};
</script>

<style scoped>
.mini-site-hero {
  position: relative;
  min-height: 100px;
  padding: 1rem;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2efe4 0%, #b8d7bf 100%);
  color: #173e29;
  text-align: center;
}

.hero-image,
.hero-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-image {
  object-fit: cover;
}

.hero-overlay {
  background: rgba(0, 0, 0, 0.6);
}

.has-image {
  color: #fff;
}

.hero-content {
  position: relative;
  max-width: 800px;
  overflow-wrap: anywhere;
}

.hero-title,
:global(#app) .hero-title {
  color: inherit;
  margin: 0;
  font-size: 14pt;
  line-height: 1.3;
}

.hero-subtitle {
  color: inherit;
  margin: 0;
  font-size: 10pt;
}

@media (max-width: 768px) {
  .mini-site-hero {
    min-height: 90px;
  }

  .hero-title,
  :global(#app) .hero-title {
    font-size: 12pt;
  }
}
</style>
