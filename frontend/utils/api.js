// frontend/utils/api.js (修改版，用于更明确的错误处理)
const BASE_URL = 'https://beverage-167990-7-1363892886.sh.run.tcloudbase.com'; // 您的后端基地址

/**
 * 发送不带Token的普通请求 (保持不变)
 * @param {object} options - 请求配置 {url, method, data, contentType}
 */
const request = (options) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': options.contentType || 'application/json'
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          // 【修正点】更详细的错误信息，特别是针对重定向
          let errorMessage = res.data ? (res.data.message || JSON.stringify(res.data)) : `HTTP状态码: ${res.statusCode}`;
          if (res.statusCode === 308) {
            errorMessage = `请求被永久重定向 (${res.statusCode})，请检查后端URL配置是否正确 (例如HTTPS/HTTP，或路径斜杠)。`;
          }
          wx.showToast({ title: `请求失败: ${errorMessage}`, icon: 'none', duration: 3000 });
          reject(res.data || { message: errorMessage });
        }
      },
      fail: (err) => {
        console.error(`请求失败: ${options.url}`, err);
        wx.showToast({
          title: '网络请求失败，请检查网络',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};


/**
 * 发送带Token的认证请求 (修改版，用于更明确的错误处理)
 * @param {object} options - 请求配置 {url, method, data, contentType}
 */
const requestWithAuth = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token');
    if (!token) {
      reject({ message: "未找到Token，请重新登录" });
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': options.contentType || 'application/json',
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          let errorMessage = res.data ? (res.data.message || JSON.stringify(res.data)) : `HTTP状态码: ${res.statusCode}`;
          if (res.statusCode === 401) { // Unauthorized, token might be expired
              wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' });
              wx.removeStorageSync('token');
              wx.reLaunch({ url: '/pages/index/index' });
              reject('Unauthorized');
          } else if (res.statusCode === 308) { // 【新增】处理 308
              errorMessage = `请求被永久重定向 (${res.statusCode})，请检查后端URL配置是否正确 (例如HTTPS/HTTP，或路径斜杠)。`;
              wx.showToast({ title: `认证请求失败: ${errorMessage}`, icon: 'none', duration: 3000 });
              reject({ message: errorMessage });
          } else {
              wx.showToast({ title: `认证请求失败: ${errorMessage}`, icon: 'none', duration: 3000 });
              reject(res.data || { message: errorMessage });
          }
        }
      },
      fail: (err) => {
        console.error(`认证请求失败: ${options.url}`, err);
        wx.showToast({
          title: '网络请求失败，请检查网络',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};

module.exports = {
  BASE_URL,
  request,
  requestWithAuth
};