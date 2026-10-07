import { toast } from 'sonner';

// Notification history with Sonner feedback
// Persist notifications in localStorage under key 'app_notifications'

const STORAGE_KEY = 'app_notifications_v1';

function _load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error('notificationsHelper load error', e);
    return [];
  }
}

function _save(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (e) {
    console.error('notificationsHelper save error', e);
  }
}

export function listNotifications() {
  return _load();
}

export function unreadCount() {
  return _load().filter(n => !n.read).length;
}

// Notification object: { id, type, priority, message, data, read, created_at }
export function pushNotification(notification) {
  const list = _load();
  // Avoid duplicates for same period/type: use id as unique key
  if (notification.id && list.find(n => n.id === notification.id)) return;
  notification.created_at = new Date().toISOString();
  notification.read = false;
  list.unshift(notification);
  _save(list);
  const show = { success: toast.success, error: toast.error, warning: toast.warning, info: toast.info }[notification.type] || toast;
  show(notification.message, { id: notification.id });
}

export function markAllRead() {
  const list = _load().map(n => ({ ...n, read: true }));
  _save(list);
}

export function markRead(id) {
  const list = _load().map(n => n.id === id ? { ...n, read: true } : n);
  _save(list);
}

export function removeNotification(id) {
  const list = _load().filter(n => n.id !== id);
  _save(list);
}

export function clearNotifications() {
  _save([]);
}

export default {
  listNotifications,
  unreadCount,
  pushNotification,
  markAllRead,
  markRead,
  removeNotification,
  clearNotifications
};
