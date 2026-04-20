import 'vuetify/styles';
import { createVuetify } from 'vuetify';

export const vuetify = createVuetify({
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
