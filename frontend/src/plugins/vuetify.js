import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

export const vuetify = createVuetify({
  components,
  directives,
  defaults: {
    VBtn: {
      ripple: false,
    },
    VCard: {
      elevation: 0,
    },
    VChip: {
      size: 'small',
    },
  },
});
