import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createI18n } from 'vue-i18n';

import ResetSessionPasswordDialog from './ResetSessionPasswordDialog.vue';
import SessionPasswordDialog from './SessionPasswordDialog.vue';
import VerifySessionPasswordDialog from './VerifySessionPasswordDialog.vue';
import {
  getSessionPasswordHint,
  removeSessionPassword,
  resetSessionPassword,
  setSessionPassword,
  updateSessionPassword,
  verifySessionPassword,
} from '../../api/agent';

vi.mock('../../api/agent', () => ({
  getSessionPasswordHint: vi.fn(),
  removeSessionPassword: vi.fn(),
  resetSessionPassword: vi.fn(),
  setSessionPassword: vi.fn(),
  updateSessionPassword: vi.fn(),
  verifySessionPassword: vi.fn(),
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en: {} },
  missingWarn: false,
  fallbackWarn: false,
});

const global = {
  plugins: [i18n],
};

const textInput = (index: number) => document.body.querySelectorAll('input')[index] as HTMLInputElement;
const setInputValue = async (index: number, value: string) => {
  const input = textInput(index);
  input.value = value;
  input.dispatchEvent(new Event('input'));
  await nextTick();
};
const buttonByText = (text: string) => {
  const button = Array.from(document.body.querySelectorAll('button')).find((element) => element.textContent?.trim() === text);
  if (!button) throw new Error(`Button not found: ${text}`);
  return button;
};

describe('session password dialogs', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    vi.mocked(getSessionPasswordHint).mockResolvedValue({ hint: null });
    vi.mocked(setSessionPassword).mockResolvedValue({ has_password: true });
    vi.mocked(updateSessionPassword).mockResolvedValue({ has_password: true });
    vi.mocked(removeSessionPassword).mockResolvedValue({ has_password: false });
    vi.mocked(verifySessionPassword).mockResolvedValue({ valid: true });
    vi.mocked(resetSessionPassword).mockResolvedValue({ has_password: true });
  });

  afterEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('sets a session password and emits protected state', async () => {
    const wrapper = mount(SessionPasswordDialog, {
      attachTo: document.body,
      props: { open: true, sessionId: 'session-1', mode: 'set' },
      global,
    });

    await setInputValue(0, 'Secret1');
    await setInputValue(1, 'Secret1');
    await setInputValue(2, 'private hint');
    await buttonByText('Set session password').click();
    await flushPromises();

    expect(setSessionPassword).toHaveBeenCalledWith('session-1', { password: 'Secret1', hint: 'private hint' });
    expect(wrapper.emitted('success')).toEqual([[true]]);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('updates and removes a session password through the selected mode', async () => {
    const updateWrapper = mount(SessionPasswordDialog, {
      attachTo: document.body,
      props: { open: true, sessionId: 'session-1', mode: 'update' },
      global,
    });

    await setInputValue(0, 'Oldsecret1');
    await setInputValue(1, 'Newsecret1');
    await setInputValue(2, 'Newsecret1');
    await buttonByText('Change session password').click();
    await flushPromises();

    expect(updateSessionPassword).toHaveBeenCalledWith('session-1', {
      old_password: 'Oldsecret1',
      new_password: 'Newsecret1',
      hint: undefined,
    });
    expect(updateWrapper.emitted('success')).toEqual([[true]]);

    updateWrapper.unmount();
    document.body.innerHTML = '';

    const removeWrapper = mount(SessionPasswordDialog, {
      attachTo: document.body,
      props: { open: true, sessionId: 'session-1', mode: 'remove' },
      global,
    });

    await setInputValue(0, 'Oldsecret1');
    await buttonByText('Remove session password').click();
    await flushPromises();

    expect(removeSessionPassword).toHaveBeenCalledWith('session-1', { password: 'Oldsecret1' });
    expect(removeWrapper.emitted('success')).toEqual([[false]]);
  });

  it('loads hints, rejects incorrect passwords, and unlocks on a valid password', async () => {
    vi.mocked(getSessionPasswordHint).mockResolvedValue({ hint: 'lab notebook' });
    vi.mocked(verifySessionPassword)
      .mockResolvedValueOnce({ valid: false })
      .mockResolvedValueOnce({ valid: true });

    const wrapper = mount(VerifySessionPasswordDialog, {
      attachTo: document.body,
      props: { open: false, sessionId: 'session-1' },
      global,
    });
    await wrapper.setProps({ open: true });
    await flushPromises();

    expect(getSessionPasswordHint).toHaveBeenCalledWith('session-1');
    expect(document.body.textContent).toContain('lab notebook');

    await setInputValue(0, 'wrong');
    await buttonByText('Confirm').click();
    await flushPromises();

    expect(document.body.textContent).toContain('Incorrect session password');
    expect(wrapper.emitted('success')).toBeUndefined();

    await setInputValue(0, 'correct');
    await buttonByText('Confirm').click();
    await flushPromises();

    expect(verifySessionPassword).toHaveBeenLastCalledWith('session-1', { password: 'correct' });
    expect(wrapper.emitted('success')).toEqual([[true]]);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('propagates reset results from the verification dialog', async () => {
    vi.mocked(resetSessionPassword).mockResolvedValue({ has_password: false });
    const wrapper = mount(VerifySessionPasswordDialog, {
      attachTo: document.body,
      props: { open: false, sessionId: 'session-1' },
      global,
    });
    await wrapper.setProps({ open: true });
    await flushPromises();

    await buttonByText('Forgot session password?').click();
    await flushPromises();
    await setInputValue(1, 'account-secret');
    await buttonByText('Reset session password').click();
    await flushPromises();

    expect(resetSessionPassword).toHaveBeenCalledWith('session-1', {
      account_password: 'account-secret',
      new_password: undefined,
      hint: undefined,
    });
    expect(wrapper.emitted('success')).toEqual([[false]]);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('resets with a new password only after confirmation matches', async () => {
    const wrapper = mount(ResetSessionPasswordDialog, {
      attachTo: document.body,
      props: { open: true, sessionId: 'session-1' },
      global,
    });

    await setInputValue(0, 'account-secret');
    await setInputValue(1, 'next');
    expect(buttonByText('Reset session password').getAttribute('disabled')).toBe('');

    await setInputValue(1, 'Next1');
    await setInputValue(2, 'Mismatch1');
    expect(document.body.textContent).toContain('Session passwords do not match');

    await setInputValue(2, 'Next1');
    await setInputValue(3, 'safe reminder');
    await buttonByText('Reset session password').click();
    await flushPromises();

    expect(document.body.textContent).toContain('Do not include the password itself');
    expect(resetSessionPassword).toHaveBeenCalledWith('session-1', {
      account_password: 'account-secret',
      new_password: 'Next1',
      hint: 'safe reminder',
    });
    expect(wrapper.emitted('success')).toEqual([[true]]);
  });
});
