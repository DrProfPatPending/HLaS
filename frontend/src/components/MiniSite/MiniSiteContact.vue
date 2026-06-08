<template>
  <div class="mini-site-page contact-page">
    <section class="page-header">
      <h1>Contact Us</h1>
      <p v-if="subheading" class="subheading">{{ subheading }}</p>
    </section>

    <section class="contact-content">
      <div class="contact-container">
        <div v-if="content" class="contact-text" v-html="content" />
        <div v-else class="contact-default">
          <p>Get in touch with {{ clubName }}. We'd love to hear from you.</p>

          <div class="contact-info">
            <div v-if="contactEmail" class="contact-method">
              <h3>📧 Email</h3>
              <a :href="`mailto:${contactEmail}`">{{ contactEmail }}</a>
            </div>

            <div v-if="contactPhone" class="contact-method">
              <h3>📞 Phone</h3>
              <a :href="`tel:${contactPhone}`">{{ contactPhone }}</a>
            </div>

            <div v-if="contactAddress" class="contact-method">
              <h3>📍 Address</h3>
              <p>{{ contactAddress }}</p>
            </div>
          </div>

          <div v-if="showContactForm" class="contact-form-section">
            <h3>Send us a Message</h3>
            <form class="contact-form" @submit.prevent="submitForm">
              <div class="form-group">
                <label for="name">Name *</label>
                <input v-model="formData.name" type="text" id="name" name="name" required />
              </div>

              <div class="form-group">
                <label for="email">Email *</label>
                <input v-model="formData.email" type="email" id="email" name="email" required />
              </div>

              <div class="form-group">
                <label for="subject">Subject</label>
                <input v-model="formData.subject" type="text" id="subject" name="subject" />
              </div>

              <div class="form-group">
                <label for="message">Message *</label>
                <textarea v-model="formData.message" id="message" name="message" rows="5" required />
              </div>

              <button type="submit" class="submit-button">Send Message</button>
            </form>
          </div>

          <div v-else class="contact-form-section">
            <h3>Email Us</h3>
            <p v-if="contactEmail" class="email-only-copy">
              Please email us directly at
              <a :href="`mailto:${contactEmail}`">{{ contactEmail }}</a>.
            </p>
            <p v-else class="email-only-copy">
              Please use the club email address shown above to contact us.
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'MiniSiteContact',
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
    contactEmail: {
      type: String,
      default: '',
    },
    contactPhone: {
      type: String,
      default: '',
    },
    contactAddress: {
      type: String,
      default: '',
    },
    contactDisplayMode: {
      type: String,
      default: 'form',
    },
  },
  computed: {
    showContactForm() {
      return this.contactDisplayMode !== 'email';
    },
  },
  data() {
    return {
      formData: {
        name: '',
        email: '',
        subject: '',
        message: '',
      },
    };
  },
  methods: {
    async submitForm() {
      // TODO: Implement form submission to backend
      alert('Thank you for your message. We will get back to you soon.');
      this.resetForm();
    },
    resetForm() {
      this.formData = {
        name: '',
        email: '',
        subject: '',
        message: '',
      };
    },
  },
};
</script>

<style scoped>
.contact-page {
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

.contact-content {
  padding: 3rem 2rem;
  background: white;
}

.contact-container {
  max-width: 900px;
  margin: 0 auto;
}

.contact-text {
  color: #333;
  line-height: 1.8;
  font-size: 1rem;
}

.contact-default p:first-of-type {
  margin-bottom: 2rem;
  color: #555;
  line-height: 1.7;
}

.contact-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.contact-method {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #2d6a45;
}

.contact-method h3 {
  margin: 0 0 0.75rem 0;
  color: #1a472a;
  font-size: 1.1rem;
}

.contact-method a {
  color: #2d6a45;
  text-decoration: none;
  font-weight: bold;
  transition: color 0.2s;
}

.contact-method a:hover {
  color: #1a472a;
}

.contact-method p {
  margin: 0;
  color: #555;
  line-height: 1.6;
}

.contact-form-section h3 {
  color: #1a472a;
  font-size: 1.3rem;
  margin-bottom: 1.5rem;
}

.email-only-copy {
  color: #555;
  line-height: 1.7;
}

.email-only-copy a {
  color: #2d6a45;
  font-weight: bold;
  text-decoration: none;
}

.contact-form {
  background: #f9f9f9;
  padding: 2rem;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #1a472a;
  font-weight: bold;
  font-size: 0.95rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1rem;
  color: #333;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #2d6a45;
  box-shadow: 0 0 0 3px rgba(45, 106, 69, 0.1);
}

.submit-button {
  background: linear-gradient(135deg, #2d6a45 0%, #1a472a 100%);
  color: white;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.submit-button:active {
  transform: translateY(0);
}

@media (max-width: 768px) {
  .page-header {
    height: 90px;
  }

  .page-header h1 {
    font-size: 12pt;
  }

  .contact-content {
    padding: 2rem 1.5rem;
  }

  .contact-info {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .contact-form {
    padding: 1.5rem;
  }
}
</style>
