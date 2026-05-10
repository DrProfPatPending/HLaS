<template>
  <div class="mini-site-page waters-page">
    <section class="page-header">
      <h1>Our Waters</h1>
      <p v-if="subheading" class="subheading">{{ subheading }}</p>
    </section>

    <section class="waters-content">
      <div class="waters-container">
        <div v-if="content" class="waters-text" v-html="content" />
        <div v-else class="waters-default">
          <p>
            {{ clubName }} has exclusive access to some of the finest fly fishing waters in the UK.
          </p>
          <h3>Available Beats</h3>
          <div class="beats-grid">
            <div class="beat-card">
              <h4>River Beat 1</h4>
              <p class="beat-info">
                <strong>Type:</strong> Chalk stream<br />
                <strong>Access:</strong> Year-round<br />
                <strong>Species:</strong> Trout
              </p>
            </div>
            <div class="beat-card">
              <h4>River Beat 2</h4>
              <p class="beat-info">
                <strong>Type:</strong> Spate stream<br />
                <strong>Access:</strong> Year-round<br />
                <strong>Species:</strong> Salmon, Trout
              </p>
            </div>
            <div class="beat-card">
              <h4>River Beat 3</h4>
              <p class="beat-info">
                <strong>Type:</strong> Lowland stream<br />
                <strong>Access:</strong> Summer-Autumn<br />
                <strong>Species:</strong> Trout, Grayling
              </p>
            </div>
          </div>
          <h3>Fishing Guidelines</h3>
          <ul>
            <li>Catch and release fishing is encouraged</li>
            <li>All anglers must follow local conservation regulations</li>
            <li>Respect for other members and the environment is essential</li>
            <li>Contact the club for seasonal restrictions and updates</li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'MiniSiteWaters',
  props: {
    clubName: {
      type: String,
      required: true,
    },
    content: {
      type: String,
      default: '',
    },
    subheading: {
      type: String,
      default: '',
    },
  },
};
</script>

<style scoped>
.waters-page {
  width: 100%;
}

.page-header {
  background: linear-gradient(135deg, #2d6a45 0%, #1a472a 100%);
  color: white;
  padding: 1rem;
  text-align: center;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.page-header h1 {
  margin: 0;
  font-size: 14pt;
}

.subheading {
  margin: 0;
  font-size: 10pt;
  opacity: 0.9;
}

.waters-content {
  padding: 3rem 2rem;
  background: white;
}

.waters-container {
  max-width: 900px;
  margin: 0 auto;
}

.waters-text {
  color: #333;
  line-height: 1.8;
  font-size: 1rem;
}

.waters-default p {
  color: #555;
  line-height: 1.7;
  margin-bottom: 1.5rem;
}

.waters-default h3 {
  color: #2d6a45;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.beats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.beat-card {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #2d6a45;
}

.beat-card h4 {
  margin: 0 0 1rem 0;
  color: #1a472a;
}

.beat-info {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
  line-height: 1.6;
}

.waters-default ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.waters-default li {
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
  position: relative;
  color: #555;
  line-height: 1.6;
}

.waters-default li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #2d6a45;
  font-weight: bold;
}

@media (max-width: 768px) {
  .page-header {
    height: 90px;
  }

  .page-header h1 {
    font-size: 12pt;
  }

  .waters-content {
    padding: 2rem 1.5rem;
  }

  .beats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
