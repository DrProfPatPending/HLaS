<template>
  <div class="mini-site-page join-page">
    <section class="page-header">
      <h1>Join {{ clubName }}</h1>
      <p v-if="subheading" class="subheading">{{ subheading }}</p>
    </section>

    <section class="join-content">
      <div class="join-container">
        <div v-if="content" class="join-text" v-html="content" />
        <div v-else class="join-default">
          <h2>Become a Member</h2>
          <p>
            Are you interested in joining {{ clubName }}? We welcome fly fishing enthusiasts of all skill
            levels.
          </p>

          <h3>Membership Benefits</h3>
          <div class="benefits-grid">
            <div class="benefit-item">
              <div class="benefit-icon">🎣</div>
              <h4>Exclusive Water Access</h4>
              <p>Fish our premium beats throughout the season</p>
            </div>
            <div class="benefit-item">
              <div class="benefit-icon">👨‍🏫</div>
              <h4>Expert Tuition</h4>
              <p>Regular coaching and mentoring opportunities</p>
            </div>
            <div class="benefit-item">
              <div class="benefit-icon">👥</div>
              <h4>Community</h4>
              <p>Connect with fellow passionate anglers</p>
            </div>
            <div class="benefit-item">
              <div class="benefit-icon">📅</div>
              <h4>Social Events</h4>
              <p>Participate in club outings and gatherings</p>
            </div>
          </div>

          <h3>How to Apply</h3>
          <ol class="join-steps">
            <li>Complete our membership application form</li>
            <li>Provide references from existing members</li>
            <li>Meet with the membership committee</li>
            <li>Be approved and pay your membership fee</li>
          </ol>

          <div class="join-cta">
            <p>Ready to join? Contact us or complete an application:</p>
            <a href="#" class="join-button">Start Application</a>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'MiniSiteJoin',
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
.join-page {
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

.join-content {
  padding: 3rem 2rem;
  background: white;
}

.join-container {
  max-width: 900px;
  margin: 0 auto;
}

.join-text {
  color: #333;
  line-height: 1.8;
  font-size: 1rem;
}

.join-default h2 {
  color: #1a472a;
  font-size: 1.8rem;
  margin: 0 0 1rem 0;
}

.join-default h3 {
  color: #2d6a45;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.join-default p {
  color: #555;
  line-height: 1.7;
  margin-bottom: 1.5rem;
}

.benefits-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.benefit-item {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  border-top: 3px solid #2d6a45;
}

.benefit-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.benefit-item h4 {
  color: #1a472a;
  margin: 0.5rem 0;
  font-size: 1rem;
}

.benefit-item p {
  color: #666;
  margin: 0;
  font-size: 0.9rem;
}

.join-steps {
  background: #f9f9f9;
  padding: 1.5rem 1.5rem 1.5rem 3rem;
  border-radius: 8px;
  list-style: decimal;
  margin-bottom: 2rem;
}

.join-steps li {
  margin-bottom: 0.75rem;
  color: #555;
  line-height: 1.6;
}

.join-cta {
  background: linear-gradient(135deg, #2d6a45 0%, #1a472a 100%);
  color: white;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
}

.join-cta p {
  margin: 0 0 1rem 0;
  color: white;
}

.join-button {
  display: inline-block;
  background: white;
  color: #2d6a45;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  transition: transform 0.2s, box-shadow 0.2s;
}

.join-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
  .page-header {
    height: 90px;
  }

  .page-header h1 {
    font-size: 12pt;
  }

  .join-content {
    padding: 2rem 1.5rem;
  }

  .benefits-grid {
    grid-template-columns: 1fr;
  }

  .join-default h2 {
    font-size: 1.5rem;
  }
}
</style>
