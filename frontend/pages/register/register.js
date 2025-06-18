// pages/register/register.js
// 导入新的 request 方法，而不是 requestWithAuth
import { request } from '../../utils/api'; //

Page({
  data: {
    username: '',
    password: '',
    confirmPassword: '',
    isLoading: false
  },

  onLoad: function () {
    // ...
  },

  onUsernameInput: function (e) {
    this.setData({ username: e.detail.value });
  },

  onPasswordInput: function (e) {
    this.setData({ password: e.detail.value });
  },

  onConfirmPasswordInput: function (e) {
    this.setData({ confirmPassword: e.detail.value });
  },

  onRegister: async function () {
    const { username, password, confirmPassword } = this.data;

    if (!username || !password || !confirmPassword) {
      wx.showToast({ title: '请填写所有信息', icon: 'none' });
      return;
    }

    if (password !== confirmPassword) {
      wx.showToast({ title: '两次密码输入不一致', icon: 'none' });
      return;
    }

    this.setData({ isLoading: true });
    wx.showLoading({ title: '注册中...', mask: true });

    try {
      // *** 关键修改在这里：调用 request 而不是 requestWithAuth ***
      const res = await request({ //
        url: '/api/register',
        method: 'POST',
        data: { username, password }
      });

      // 注意：你的后端 auth.py 返回的是 {code: 200, message: "注册成功"}
      if (res.code === 200) { //
        wx.hideLoading();
        wx.showToast({ title: '注册成功', icon: 'success', duration: 1500 });
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/index/index' }); // 注册成功后跳转到登录页
        }, 1500);
      } else {
        wx.hideLoading();
        wx.showToast({ title: res.message || '注册失败', icon: 'none' }); //
      }
    } catch (error) {
      wx.hideLoading();
      console.error('注册请求失败', error); //
      wx.showToast({ title: '注册失败，请稍后重试', icon: 'none' });
    } finally {
      this.setData({ isLoading: false });
    }
  },

  goToLogin: function () {
    wx.redirectTo({ url: '/pages/index/index' }); //
  }
});