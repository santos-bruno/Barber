// Registro de notificações push (FCM) — best-effort, nunca trava o app.
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { registerPushToken } from './api/client';

// Mostra a notificação mesmo com o app aberto.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

let _done = false;

export async function registerForPush() {
  // Só tenta uma vez por sessão e só em aparelho real.
  if (_done || !Device.isDevice) return;
  try {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'Avisos',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#F0C24B',
      });
    }
    const current = await Notifications.getPermissionsAsync();
    let status = current.status;
    if (status !== 'granted') {
      const asked = await Notifications.requestPermissionsAsync();
      status = asked.status;
    }
    if (status !== 'granted') return;

    // Token nativo do FCM (não precisa de projeto EAS).
    const resp = await Notifications.getDevicePushTokenAsync();
    const token = resp && resp.data ? String(resp.data) : '';
    if (token) {
      await registerPushToken({ token, platform: Platform.OS });
      _done = true;
    }
  } catch (e) {
    // push é opcional — falha silenciosa (sem Firebase/permite, apenas não registra)
  }
}
