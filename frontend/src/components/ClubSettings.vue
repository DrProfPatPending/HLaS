<template>
  <div class="club-settings-container">
    <div class="club-settings-header">
      <h2>Club Settings</h2>
      <p>Configure settings for {{ loggedInClub }}.</p>
    </div>

    <!-- Repeated at the bottom of the page. -->
    <div class="club-settings-actions club-settings-actions-top">
      <app-button type="button" inherit-style :disabled="loading || saving" @click="loadSettings">
        {{ loading ? 'Loading…' : 'Reload' }}
      </app-button>
      <app-button type="button" inherit-style :disabled="saving || loading" @click="saveSettings">
        {{ saving ? 'Saving…' : 'Save Settings' }}
      </app-button>
    </div>

    <p v-if="status" class="club-settings-status">{{ status }}</p>
    <p v-if="error" class="club-settings-error">{{ error }}</p>

    <!-- Field Order Section -->
    <section class="club-settings-section">
      <h3>Field Order</h3>
      <p class="section-description">
        Configure column order, labels and visibility for this club. The Catch Return form fields are in the
        <code>catch_return</code> context.
      </p>

      <div class="club-settings-inline-controls">
        <label for="club-field-order-context">Context:</label>
        <select
          id="club-field-order-context"
          v-model="selectedFieldOrderContext"
          class="form-input"
          :disabled="loading || !fieldOrderContextNames.length"
        >
          <option v-for="contextName in fieldOrderContextNames" :key="contextName" :value="contextName">
            {{ contextName }}
          </option>
        </select>
      </div>

      <div v-if="fieldOrderContextNames.length" class="club-settings-field-order-table-wrap">
        <table class="club-settings-table club-settings-field-order-table">
          <thead>
            <tr>
              <th class="fo-num">#</th>
              <th class="fo-field">Field</th>
              <th class="fo-label">Display As</th>
              <th class="fo-check">Show</th>
              <template v-if="!isFormFieldOrderContext">
                <th class="fo-check">Read Only</th>
                <th class="fo-size">Min Width</th>
                <th class="fo-size">Width</th>
              </template>
              <th class="fo-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(fieldName, index) in selectedFieldOrderFields" :key="`${selectedFieldOrderContext}-${fieldName}-${index}`">
              <td class="fo-num">{{ index + 1 }}</td>
              <td class="fo-field">{{ fieldName }}</td>
              <td class="fo-label">
                <input
                  type="text"
                  class="form-input"
                  :value="getFieldOrderDisplayName(fieldName)"
                  :placeholder="fieldName"
                  @input="setFieldOrderDisplayName(fieldName, $event.target.value)"
                />
              </td>
              <td class="fo-check">
                <input
                  type="checkbox"
                  :checked="isFieldOrderFieldVisible(fieldName)"
                  @change="setFieldOrderFieldVisible(fieldName, $event.target.checked)"
                />
              </td>
              <template v-if="!isFormFieldOrderContext">
                <td class="fo-check">
                  <input
                    type="checkbox"
                    :checked="isFieldOrderFieldReadOnly(fieldName)"
                    @change="setFieldOrderFieldReadOnly(fieldName, $event.target.checked)"
                  />
                </td>
                <td class="fo-size">
                  <input
                    type="number"
                    class="form-input"
                    min="0"
                    title="Minimum column width in pixels."
                    :value="getFieldOrderMinWidth(fieldName)"
                    @input="setFieldOrderMinWidth(fieldName, $event.target.value)"
                  />
                </td>
                <td class="fo-size">
                  <input
                    type="text"
                    class="form-input"
                    placeholder="flex"
                    title="Column width, e.g. 90 (pixels), 90px or 12%. Leave blank or 'flex' to size automatically."
                    :value="getFieldOrderColumnWidth(fieldName)"
                    @input="setFieldOrderColumnWidth(fieldName, $event.target.value)"
                  />
                </td>
              </template>
              <td class="club-settings-field-order-actions-cell">
                <button type="button" :disabled="index === 0" @click="moveFieldOrderToTop(index)">Top</button>
                <button type="button" :disabled="index === 0" @click="moveFieldOrderUp(index)">Up</button>
                <button type="button" :disabled="index === selectedFieldOrderFields.length - 1" @click="moveFieldOrderDown(index)">Down</button>
                <button type="button" :disabled="index === selectedFieldOrderFields.length - 1" @click="moveFieldOrderToBottom(index)">Bottom</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="section-description">No field-order contexts available for this club.</p>
    </section>

    <!-- Mini Site Section -->
    <section class="club-settings-section">
      <h3>Club Mini Site</h3>
      <p class="section-description">Create a public-facing marketing website for your club.</p>
      
      <div class="mini-site-config">
        <label class="mini-site-toggle">
          <input v-model="miniSite.enabled" type="checkbox" />
          <span class="toggle-label">{{ miniSite.enabled ? 'Enable' : 'Disable' }} Mini Site</span>
        </label>
        <p class="mini-site-hint">
          {{ miniSite.enabled ? 'Your mini site is enabled and accessible.' : 'Enable to create a public marketing page.' }}
        </p>

        <template v-if="miniSite.enabled">
          <div class="form-group">
            <label for="mini-site-title">Site Title</label>
            <input
              id="mini-site-title"
              v-model="miniSite.title"
              type="text"
              placeholder="e.g., Cambridge Trout Club"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-tagline">Tagline</label>
            <input
              id="mini-site-tagline"
              v-model="miniSite.tagline"
              type="text"
              placeholder="e.g., Premier fly fishing destination"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-description">Description</label>
            <textarea
              id="mini-site-description"
              v-model="miniSite.description"
              placeholder="Brief description of your club"
              class="form-input"
              rows="4"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-hero">Home Hero Image URL</label>
            <input
              id="mini-site-hero"
              v-model="miniSite.hero_image_url"
              type="text"
              placeholder="/api/club_hero/CLUB or https://..."
              class="form-input"
            />
            <p class="form-hint">Home page image, also used by pages that select the Home hero fallback.</p>
          </div>

          <div class="mini-site-preview">
            <strong>Mini Site URL:</strong>
            <code>{{ miniSiteUrl }}</code>
            <p class="form-hint">
              Enabled pages are available on desktop and mobile.
            </p>
          </div>

          <!-- Pages Section -->
          <div class="pages-config">
            <h4>Pages</h4>
            <p class="pages-description">Select which pages appear on your mini site.</p>
            <div class="pages-grid">
              <label v-for="page in miniSitePages" :key="page.id" class="page-checkbox">
                <input
                  v-model="miniSite.pages"
                  :value="page.id"
                  type="checkbox"
                  :disabled="!page.canDisable"
                />
                <span>{{ page.title }}</span>
                <span v-if="!page.canDisable" class="page-badge">Always enabled</span>
              </label>
            </div>
          </div>

          <div class="pages-config">
            <h4>Page Hero Images</h4>
            <div class="form-group">
              <label for="mini-site-hero-page">Page</label>
              <select id="mini-site-hero-page" v-model="selectedHeroPage" class="form-input">
                <option v-for="page in miniSiteHeroPages" :key="page.id" :value="page.id">
                  {{ page.title }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label for="mini-site-page-hero">Page Image URL (optional)</label>
              <input
                id="mini-site-page-hero"
                v-model="miniSite.page_configs[selectedHeroPage].hero_image_url"
                type="text"
                placeholder="/api/club_hero/CLUB or https://..."
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="mini-site-page-hero-fallback">When the page image is empty or cannot load</label>
              <select
                id="mini-site-page-hero-fallback"
                v-model="miniSite.page_configs[selectedHeroPage].hero_fallback"
                class="form-input"
              >
                <option value="home">Use Home hero, then light green banner</option>
                <option value="banner">Use light green banner</option>
              </select>
              <p class="form-hint">
                Leave the page image empty and select the green banner to show no image.
                Images use a dark overlay for readable text on desktop and mobile.
              </p>
            </div>
          </div>

          <div class="pages-config">
            <h4>Page Content</h4>
            <p class="pages-description">
              Leave fields blank to use the page's built-in text. Basic HTML such as paragraphs, headings,
              emphasis, lists and links is supported; scripts, styles and unsupported tags are removed.
            </p>
            <div class="form-group">
              <label for="mini-site-content-page">Page</label>
              <select id="mini-site-content-page" v-model="selectedContentPage" class="form-input">
                <option v-for="page in miniSitePages" :key="page.id" :value="page.id">
                  {{ page.title }}
                </option>
              </select>
            </div>
            <p class="form-hint" role="status">
              {{ pageContentStatus(selectedContentPage) }}
            </p>
            <div class="form-group">
              <label for="mini-site-page-headline">
                {{ selectedContentPage === 'home' ? 'Home Headline' : 'Page Heading' }}
              </label>
              <input
                id="mini-site-page-headline"
                v-model="miniSite.page_configs[selectedContentPage].headline"
                type="text"
                :placeholder="selectedContentPage === 'home' ? 'Text shown after Welcome to' : 'Leave blank to use the built-in heading'"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="mini-site-page-subheading">Page Subheading</label>
              <input
                id="mini-site-page-subheading"
                v-model="miniSite.page_configs[selectedContentPage].subheading"
                type="text"
                placeholder="Optional short line beneath the heading"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="mini-site-page-content">Page Body Text</label>
              <textarea
                id="mini-site-page-content"
                v-model="miniSite.page_configs[selectedContentPage].content"
                placeholder="Leave blank to use the built-in page text"
                class="form-input"
                rows="8"
              />
            </div>
            <button
              type="button"
              class="reset-page-content-button"
              :disabled="!hasCustomPageContent(selectedContentPage)"
              @click="resetPageContent(selectedContentPage)"
            >
              Reset to built-in text
            </button>
          </div>

          <div class="form-group">
            <label>Home Feature Panels</label>
            <div class="pages-grid">
              <label class="page-checkbox">
                <input v-model="miniSite.show_exclusive_access" type="checkbox" />
                <span>Exclusive Access panel</span>
              </label>
              <label class="page-checkbox">
                <input v-model="miniSite.show_community" type="checkbox" />
                <span>Community panel</span>
              </label>
              <label class="page-checkbox">
                <input v-model="miniSite.show_learning" type="checkbox" />
                <span>Learning panel</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label for="contact-display-mode">Contact Page Display</label>
            <select
              id="contact-display-mode"
              v-model="miniSite.contact_display_mode"
              class="form-input"
            >
              <option value="form">Show contact form</option>
              <option value="email">Show email address only</option>
            </select>
            <p class="form-hint">Choose whether visitors see a form or just your registered club email address.</p>
          </div>

          <div class="form-group">
            <label class="page-checkbox">
              <input v-model="miniSite.show_direct_email_link" type="checkbox" />
              <span>Direct Email Link?</span>
            </label>
            <p class="form-hint">When email-only mode is selected, show or hide the secondary "Email Us" block.</p>
          </div>
        </template>
      </div>
    </section>

    <div class="club-settings-actions">
      <app-button type="button" inherit-style :disabled="loading || saving" @click="loadSettings">
        {{ loading ? 'Loading…' : 'Reload' }}
      </app-button>
      <app-button type="button" inherit-style :disabled="saving || loading" @click="saveSettings">
        {{ saving ? 'Saving…' : 'Save Settings' }}
      </app-button>
      <span v-if="status" class="club-settings-status club-settings-actions-message">{{ status }}</span>
      <span v-if="error" class="club-settings-error club-settings-actions-message">{{ error }}</span>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE_URL, store } from '../store.js';
import AppButton from './ui/AppButton.vue';

const CATCH_RETURN_FIELDS = [
  { key: 'sessionDate', label: 'Date' },
  { key: 'beatId', label: 'Beat ID' },
  { key: 'smallTrout', label: 'Small Trout' },
  { key: 'mediumTrout', label: 'Medium Trout' },
  { key: 'largeTrout', label: 'Large Trout' },
  { key: 'smallGrayling', label: 'Small Grayling' },
  { key: 'mediumGrayling', label: 'Medium Grayling' },
  { key: 'largeGrayling', label: 'Large Grayling' },
  { key: 'otherFish', label: 'Other Fish' },
  { key: 'fliesUsed', label: 'Flies Used' },
  { key: 'weatherConditions', label: 'Weather Conditions' },
  { key: 'predatorDamage', label: 'Predator Damage' },
  { key: 'comments', label: 'Comments' },
];

// Catch Return labels and visibility live in this Field Order context. Until a club
// saves it, visibility falls back to the older catchReturnFieldVisibility setting.
const CATCH_RETURN_FIELD_ORDER_CONTEXT = 'catch_return';

const MINI_SITE_PAGES = [
  { id: 'home', title: 'Home', canDisable: false },
  { id: 'about', title: 'About Us', canDisable: true },
  { id: 'waters', title: 'Our Waters', canDisable: true },
  { id: 'news', title: 'News', canDisable: true },
  { id: 'join', title: 'Join', canDisable: true },
  { id: 'contact', title: 'Contact Us', canDisable: true },
];

function defaultVisibility() {
  return Object.fromEntries(CATCH_RETURN_FIELDS.map(field => [field.key, true]));
}

function defaultMiniSite() {
  return {
    enabled: false,
    title: '',
    tagline: '',
    description: '',
    hero_image_url: '',
    show_exclusive_access: true,
    show_community: true,
    show_learning: true,
    contact_display_mode: 'form',
    show_direct_email_link: true,
    page_configs: Object.fromEntries(MINI_SITE_PAGES.map(page => [
      page.id,
      {
        hero_image_url: '',
        hero_fallback: 'home',
        headline: '',
        subheading: '',
        content: '',
      },
    ])),
    pages: ['home', 'about', 'waters', 'news', 'join', 'contact'], // All pages enabled by default
  };
}

export default {
  name: 'ClubSettings',
  components: {
    AppButton,
  },
  data() {
    return {
      loading: false,
      saving: false,
      status: '',
      error: '',
      visibility: defaultVisibility(),
      miniSite: defaultMiniSite(),
      selectedContentPage: 'home',
      selectedHeroPage: 'about',
      fieldOrder: {},
      selectedFieldOrderContext: '',
    };
  },
  computed: {
    loggedInClub: () => store.loggedInClub,
    miniSitePages: () => MINI_SITE_PAGES,
    miniSiteHeroPages: () => MINI_SITE_PAGES.filter(page => page.id !== 'home'),
    fieldOrderContextNames() {
      return Object.entries(this.fieldOrder || {})
        .filter(([, contextValue]) => Array.isArray(contextValue))
        .map(([contextName]) => contextName);
    },
    isFormFieldOrderContext() {
      // Forms have no columns, so Read Only and widths don't apply.
      return this.selectedFieldOrderContext === CATCH_RETURN_FIELD_ORDER_CONTEXT;
    },
    selectedFieldOrderFields() {
      const fields = this.fieldOrder?.[this.selectedFieldOrderContext];
      return Array.isArray(fields) ? fields : [];
    },
    miniSiteUrl() {
      const domain = window.location.origin;
      return `${domain}/club/${this.loggedInClub}/`;
    },
  },
  created() {
    this.loadSettings();
  },
  methods: {
    pageContentStatus(pageId) {
      if (this.hasCustomPageContent(pageId)) {
        return 'Custom text is set; blank fields use their built-in defaults.';
      }
      if (pageId === 'home') {
        return 'The Home body uses the site description or built-in text.';
      }
      return 'This page is using its built-in text.';
    },
    hasCustomPageContent(pageId) {
      const page = this.miniSite.page_configs?.[pageId];
      return ['headline', 'subheading', 'content'].some(field => (
        typeof page?.[field] === 'string' && page[field].trim() !== ''
      ));
    },
    resetPageContent(pageId) {
      const page = this.miniSite.page_configs?.[pageId];
      if (!page) return;
      page.headline = '';
      page.subheading = '';
      page.content = '';
    },
    resolveClubSettingsSaveErrorMessage(err) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update club settings.';
      }
      return err?.response?.data?.error || 'Unable to save club settings.';
    },
    normalizeVisibility(rawVisibility) {
      const source = rawVisibility && typeof rawVisibility === 'object' ? rawVisibility : {};
      const normalized = defaultVisibility();
      for (const field of CATCH_RETURN_FIELDS) {
        if (Object.prototype.hasOwnProperty.call(source, field.key)) {
          normalized[field.key] = Boolean(source[field.key]);
        }
      }
      return normalized;
    },
    replaceSelectedFieldOrderFields(nextFields) {
      if (!this.selectedFieldOrderContext) return;
      this.fieldOrder = {
        ...this.fieldOrder,
        [this.selectedFieldOrderContext]: nextFields,
      };
    },
    selectedFieldOrderMap(settingKey) {
      const perContext = this.fieldOrder?.[settingKey]?.[this.selectedFieldOrderContext];
      return perContext && typeof perContext === 'object' ? perContext : {};
    },
    isFieldOrderFieldVisible(fieldName) {
      return this.selectedFieldOrderMap('show_columns')?.[fieldName] !== false;
    },
    isFieldOrderFieldReadOnly(fieldName) {
      return this.selectedFieldOrderMap('read_only')?.[fieldName] === true;
    },
    getFieldOrderDisplayName(fieldName) {
      const value = this.selectedFieldOrderMap('display_names')?.[fieldName];
      return typeof value === 'string' ? value : '';
    },
    getFieldOrderMinWidth(fieldName) {
      const value = this.selectedFieldOrderMap('minimum_widths')?.[fieldName];
      return Number.isFinite(value) ? value : '';
    },
    getFieldOrderColumnWidth(fieldName) {
      const value = this.selectedFieldOrderMap('widths')?.[fieldName];
      return typeof value === 'string' ? value : '';
    },
    upsertFieldOrderMap(settingKey, fieldName, rawValue, removeWhenEmpty = true) {
      if (!this.selectedFieldOrderContext || !fieldName) return;

      const nextPerContext = {
        ...(this.fieldOrder?.[settingKey]?.[this.selectedFieldOrderContext] || {}),
      };

      if (removeWhenEmpty && (rawValue === '' || rawValue == null)) {
        delete nextPerContext[fieldName];
      } else {
        nextPerContext[fieldName] = rawValue;
      }

      this.fieldOrder = {
        ...this.fieldOrder,
        [settingKey]: {
          ...(this.fieldOrder?.[settingKey] || {}),
          [this.selectedFieldOrderContext]: nextPerContext,
        },
      };
    },
    setFieldOrderFieldVisible(fieldName, isVisible) {
      this.upsertFieldOrderMap('show_columns', fieldName, Boolean(isVisible), false);
    },
    setFieldOrderFieldReadOnly(fieldName, isReadOnly) {
      if (isReadOnly) {
        this.upsertFieldOrderMap('read_only', fieldName, true, false);
      } else {
        this.upsertFieldOrderMap('read_only', fieldName, '', true);
      }
    },
    setFieldOrderDisplayName(fieldName, displayName) {
      const value = String(displayName || '');
      this.upsertFieldOrderMap('display_names', fieldName, value, true);
    },
    setFieldOrderMinWidth(fieldName, minWidthInput) {
      const value = String(minWidthInput || '').trim();
      if (!value) {
        this.upsertFieldOrderMap('minimum_widths', fieldName, '', true);
        return;
      }
      const parsed = Number(value);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        this.upsertFieldOrderMap('minimum_widths', fieldName, '', true);
        return;
      }
      this.upsertFieldOrderMap('minimum_widths', fieldName, parsed, false);
    },
    setFieldOrderColumnWidth(fieldName, widthValue) {
      const value = String(widthValue || '').trim();
      this.upsertFieldOrderMap('widths', fieldName, value, true);
    },
    moveFieldOrderUp(index) {
      if (index <= 0) return;
      const nextFields = [...this.selectedFieldOrderFields];
      [nextFields[index - 1], nextFields[index]] = [nextFields[index], nextFields[index - 1]];
      this.replaceSelectedFieldOrderFields(nextFields);
    },
    moveFieldOrderDown(index) {
      if (index >= this.selectedFieldOrderFields.length - 1) return;
      const nextFields = [...this.selectedFieldOrderFields];
      [nextFields[index], nextFields[index + 1]] = [nextFields[index + 1], nextFields[index]];
      this.replaceSelectedFieldOrderFields(nextFields);
    },
    moveFieldOrderToTop(index) {
      if (index <= 0) return;
      const nextFields = [...this.selectedFieldOrderFields];
      const [entry] = nextFields.splice(index, 1);
      nextFields.unshift(entry);
      this.replaceSelectedFieldOrderFields(nextFields);
    },
    moveFieldOrderToBottom(index) {
      if (index >= this.selectedFieldOrderFields.length - 1) return;
      const nextFields = [...this.selectedFieldOrderFields];
      const [entry] = nextFields.splice(index, 1);
      nextFields.push(entry);
      this.replaceSelectedFieldOrderFields(nextFields);
    },
    seedCatchReturnVisibility() {
      if (!Array.isArray(this.fieldOrder?.[CATCH_RETURN_FIELD_ORDER_CONTEXT])) return;
      const showColumns = this.fieldOrder.show_columns || {};
      const existing = showColumns[CATCH_RETURN_FIELD_ORDER_CONTEXT];
      if (existing && typeof existing === 'object') return;
      this.fieldOrder = {
        ...this.fieldOrder,
        show_columns: {
          ...showColumns,
          [CATCH_RETURN_FIELD_ORDER_CONTEXT]: this.normalizeVisibility(this.visibility),
        },
      };
    },
    catchReturnVisibilityForSave() {
      // Keep the older setting in step with Field Order, so older code still shows the same fields.
      const configured = this.fieldOrder?.show_columns?.[CATCH_RETURN_FIELD_ORDER_CONTEXT];
      if (!configured || typeof configured !== 'object') {
        return this.normalizeVisibility(this.visibility);
      }
      return Object.fromEntries(CATCH_RETURN_FIELDS.map(field => [field.key, configured[field.key] !== false]));
    },
    loadSettings() {
      this.loading = true;
      this.error = '';
      this.status = '';
      this.miniSite = defaultMiniSite();
      this.fieldOrder = {};
      this.selectedFieldOrderContext = '';

      // Load the older catch return visibility and the field order together, so the
      // catch_return context can be seeded from the older setting.
      const visibilityRequest = axios
        .get(`${API_BASE_URL}/club-settings`, {
          params: { club: this.loggedInClub },
        })
        .then(res => {
          const visibility = res?.data?.settings?.catchReturnFieldVisibility;
          this.visibility = this.normalizeVisibility(visibility);
        })
        .catch(err => {
          this.visibility = defaultVisibility();
          this.error = err?.response?.data?.error || 'Unable to load club settings.';
        });

      const fieldOrderRequest = axios
        .get(`${API_BASE_URL}/club-field-order`, {
          params: { club: this.loggedInClub },
        })
        .then(res => {
          const loaded = res?.data?.field_order;
          this.fieldOrder = loaded && typeof loaded === 'object' ? loaded : {};
          if (!this.fieldOrder[this.selectedFieldOrderContext]) {
            this.selectedFieldOrderContext = this.fieldOrderContextNames[0] || '';
          }
        })
        .catch(err => {
          this.fieldOrder = {};
          if (!this.error) {
            this.error = err?.response?.data?.error || 'Unable to load club field-order settings.';
          }
        });

      Promise.all([visibilityRequest, fieldOrderRequest]).then(() => {
        this.seedCatchReturnVisibility();
      });

      // Load mini site settings
      axios
        .get(`${API_BASE_URL}/mini-site`, {
          params: { club: this.loggedInClub },
        })
        .then(res => {
          const pages = Array.isArray(res?.data?.pages) ? res.data.pages : [];
          const pageConfigs = pages.reduce((acc, page) => {
            if (page && page.id) {
              acc[page.id] = { ...acc[page.id], ...page };
            }
            return acc;
          }, defaultMiniSite().page_configs);

          // Extract enabled page IDs from the pages array
          const enabledPageIds = pages.length
            ? pages.filter(p => p.enabled).map(p => p.id)
            : ['home', 'about', 'waters', 'news', 'join', 'contact'];
          
          this.miniSite = {
            enabled: res?.data?.enabled || false,
            title: res?.data?.title || '',
            tagline: res?.data?.tagline || '',
            description: res?.data?.description || '',
            hero_image_url: res?.data?.hero_image_url || '',
            show_exclusive_access: pageConfigs.home?.show_exclusive_access !== false,
            show_community: pageConfigs.home?.show_community !== false,
            show_learning: pageConfigs.home?.show_learning !== false,
            contact_display_mode: res?.data?.contact_display_mode || 'form',
            show_direct_email_link: pageConfigs.contact?.show_direct_email_link !== false,
            page_configs: pageConfigs,
            pages: enabledPageIds,
          };
        })
        .catch(err => {
          // Mini site endpoint not available or not configured, that's ok
          this.miniSite = defaultMiniSite();
        })
        .finally(() => {
          this.loading = false;
        });
    },
    saveSettings() {
      this.saving = true;
      this.error = '';
      this.status = '';

      const catchReturnPayload = {
        club: this.loggedInClub,
        settings: {
          catchReturnFieldVisibility: this.catchReturnVisibilityForSave(),
        },
      };

      // Build full page configs for API so page-specific content and settings are persisted.
      const enabledPages = new Set(this.miniSite.pages || []);
      const pagesArray = MINI_SITE_PAGES.map(page => {
        const existing = this.miniSite.page_configs?.[page.id] || {};
        const pagePayload = {
          id: page.id,
          enabled: page.id === 'home' ? true : enabledPages.has(page.id),
        };

        for (const field of ['content', 'headline', 'subheading', 'body_text']) {
          if (typeof existing[field] === 'string' && existing[field].trim() !== '') {
            pagePayload[field] = existing[field];
          }
        }

        if (page.id === 'home') {
          pagePayload.show_exclusive_access = this.miniSite.show_exclusive_access !== false;
          pagePayload.show_community = this.miniSite.show_community !== false;
          pagePayload.show_learning = this.miniSite.show_learning !== false;
        }

        if (page.id === 'contact') {
          pagePayload.display_mode = this.miniSite.contact_display_mode || 'form';
          pagePayload.show_direct_email_link = this.miniSite.show_direct_email_link !== false;
        }

        if (page.id !== 'home') {
          pagePayload.hero_image_url = (existing.hero_image_url || '').trim();
          pagePayload.hero_fallback = existing.hero_fallback || 'home';
        }

        return pagePayload;
      });
      
      const miniSitePayload = {
        club: this.loggedInClub,
        enabled: this.miniSite.enabled,
        title: this.miniSite.title,
        tagline: this.miniSite.tagline,
        description: this.miniSite.description,
        hero_image_url: this.miniSite.hero_image_url,
        contact_display_mode: this.miniSite.contact_display_mode || 'form',
        pages: pagesArray, // Send the list of enabled page IDs
      };

        const fieldOrderPayload = {
          club: this.loggedInClub,
          field_order: this.fieldOrder,
        };

      // Save both settings in parallel
      Promise.all([
        axios.put(`${API_BASE_URL}/club-settings`, catchReturnPayload),
        axios.put(`${API_BASE_URL}/mini-site`, miniSitePayload),
          axios.put(`${API_BASE_URL}/club-field-order`, fieldOrderPayload),
      ])
        .then(() => {
          this.status = 'Club settings saved.';
        })
        .catch(err => {
          this.error = this.resolveClubSettingsSaveErrorMessage(err);
        })
        .finally(() => {
          this.saving = false;
        });
    },
  },
};
</script>

<style scoped>
.club-settings-header {
  margin-bottom: 12px;
}

.club-settings-header h2 {
  margin: 0;
}

.club-settings-header p {
  margin: 8px 0 0;
  color: #475569;
}

.club-settings-section {
  margin-bottom: 2rem;
}

.club-settings-section h3 {
  margin: 0 0 10px;
  color: #1a472a;
}

.club-settings-inline-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.club-settings-inline-controls .form-input {
  max-width: 360px;
}

.club-settings-field-order-table-wrap {
  overflow-x: auto;
}

.club-settings-field-order-actions-cell {
  white-space: nowrap;
}

.section-description {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 9.5pt;
}

.club-settings-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin-bottom: 1rem;
}

.club-settings-table th,
.club-settings-table td {
  border: 1px solid #d7dce2;
  padding: 9px 10px;
  text-align: left;
}

.club-settings-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.club-settings-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.club-settings-toggle input[type="checkbox"] {
  cursor: pointer;
}

/* Mini Site Styles */
.mini-site-config {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #2d6a45;
}

.mini-site-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1rem;
  cursor: pointer;
}

.mini-site-toggle input[type="checkbox"] {
  cursor: pointer;
  width: 20px;
  height: 20px;
}

.toggle-label {
  font-weight: 600;
  color: #1a472a;
  font-size: 10.5pt;
}

.mini-site-hint {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 9pt;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #17324d;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 10pt;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #2d6a45;
  box-shadow: 0 0 4px rgba(45, 106, 69, 0.2);
}

.form-hint {
  margin: 0.5rem 0 0 0;
  color: #999;
  font-size: 8.5pt;
}

.mini-site-preview {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
  border: 1px solid #d0d0d0;
}

.mini-site-preview strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 10pt;
  color: #17324d;
}

.mini-site-preview code {
  background: #f0f0f0;
  padding: 0.5rem;
  border-radius: 4px;
  display: block;
  word-break: break-all;
  font-family: monospace;
  font-size: 9.5pt;
  color: #2d6a45;
}

/* Pages Configuration */
.pages-config {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
  border: 1px solid #d0d0d0;
}

.pages-config h4 {
  margin: 0 0 0.5rem 0;
  color: #1a472a;
  font-size: 10pt;
}

.pages-description {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 9pt;
}

.reset-page-content-button {
  padding: 0.5rem 0.75rem;
  border: 1px solid #999;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
}

.reset-page-content-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.pages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.page-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.75rem;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  transition: background 0.2s, border-color 0.2s;
}

.page-checkbox:hover:not(:has(input:disabled)) {
  background: #f0f0f0;
  border-color: #2d6a45;
}

.page-checkbox input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

.page-checkbox input[type="checkbox"]:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.page-checkbox span:first-of-type {
  flex: 1;
  font-size: 10pt;
  font-weight: 500;
  color: #333;
}

.page-badge {
  font-size: 7.5pt;
  background: #2d6a45;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 2px;
  white-space: nowrap;
  font-weight: 600;
}

.page-checkbox:has(input:disabled) {
  opacity: 0.7;
}


.club-settings-actions {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.club-settings-actions-top {
  margin: 0 0 12px;
}

.club-settings-actions .club-settings-actions-message {
  margin: 0 0 0 4px;
}

.club-settings-status {
  margin: 0 0 10px;
  color: #21633a;
  font-weight: 600;
}

.club-settings-error {
  margin: 0 0 10px;
  color: #b42318;
  font-weight: 600;
}

/* Typography: one scale for the page. The #app prefix outranks the global
   App.vue heading sizes and the #app .form-group rules written for
   Newsletters (13px fields, monospace textareas). */
.club-settings-container {
  font-size: 10pt;
}

#app .club-settings-container h2 {
  font-size: 13pt;
}

#app .club-settings-container h3 {
  font-size: 11pt;
}

#app .club-settings-container h4 {
  font-size: 10pt;
}

#app .club-settings-container .club-settings-header p {
  font-size: 10pt;
}

#app .club-settings-container .form-group label {
  margin-bottom: 4px;
  font-size: 9.5pt;
  font-weight: 600;
  color: #17324d;
}

#app .club-settings-container .form-group input,
#app .club-settings-container .form-group textarea,
#app .club-settings-container .form-group select,
#app .club-settings-container .form-input {
  padding: 6px 8px;
  font-family: inherit;
  font-size: 10pt;
}

/* Field Order table: size columns to their content so it fits a 1080p screen. */
#app .club-settings-field-order-table {
  table-layout: auto;
}

#app .club-settings-field-order-table th,
#app .club-settings-field-order-table td {
  padding: 4px 6px;
  vertical-align: middle;
}

#app .club-settings-field-order-table th {
  font-size: 9pt;
  white-space: nowrap;
}

#app .club-settings-field-order-table .fo-num,
#app .club-settings-field-order-table .fo-check,
#app .club-settings-field-order-table .fo-size,
#app .club-settings-field-order-table .fo-actions {
  width: 1%;
  white-space: nowrap;
}

#app .club-settings-field-order-table .fo-num {
  text-align: right;
  color: #64748b;
}

#app .club-settings-field-order-table .fo-check {
  text-align: center;
}

#app .club-settings-field-order-table .fo-check input {
  margin: 0;
}

#app .club-settings-field-order-table .fo-field {
  overflow-wrap: anywhere;
}

#app .club-settings-field-order-table .form-input {
  min-width: 0;
  padding: 3px 6px;
  font-size: 9.5pt;
}

#app .club-settings-field-order-table .fo-label .form-input {
  min-width: 140px;
}

#app .club-settings-field-order-table .fo-size .form-input {
  width: 70px;
}

#app .club-settings-field-order-table .club-settings-field-order-actions-cell button {
  margin: 0 2px 0 0;
  padding: 2px 7px;
  font-size: 8.5pt;
  line-height: 1.4;
}
</style>
