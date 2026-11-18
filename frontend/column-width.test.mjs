import assert from 'node:assert/strict';
import test from 'node:test';
import { columnWidthStyle, columnWidthValue, columnMinWidthValue } from './src/columnWidth.js';

test('Field Order widths become valid CSS widths', () => {
  // Bare numbers (as typed into Club Settings) are pixels.
  assert.equal(columnWidthValue('90'), '90px');
  assert.equal(columnWidthValue(' 50 '), '50px');
  assert.equal(columnWidthValue(120), '120px');
  // CSS lengths pass through.
  assert.equal(columnWidthValue('90px'), '90px');
  assert.equal(columnWidthValue('12%'), '12%');
  assert.equal(columnWidthValue('8EM'), '8em');
  // Automatic sizing and rubbish give no width.
  for (const raw of ['flex', 'auto', '', '   ', '0', '-5', 'wide', null, undefined, {}]) {
    assert.equal(columnWidthValue(raw), '', `width ${JSON.stringify(raw)}`);
  }
  assert.equal(columnMinWidthValue(90), '90px');
  assert.equal(columnMinWidthValue('120'), '120px');
});

test('A configured width wins over the minimum width', () => {
  assert.deepEqual(columnWidthStyle('90', 120), { width: '90px' });
  assert.deepEqual(columnWidthStyle('flex', 120), { minWidth: '120px' });
  assert.deepEqual(columnWidthStyle('', '80'), { minWidth: '80px' });
  assert.deepEqual(columnWidthStyle(undefined, undefined), {});
});
