// pages/profile/profile.js
import { requestWithAuth } from '../../utils/api.js';

Page({
  data: {
    userInfo: null, // 用于存储从后端获取的用户信息
  },

  /**
   * 使用 onShow 生命周期函数
   * 这样每次切换到“我的”页面时，都会重新获取用户信息
   */
  onShow: function () {
    this.fetchUserProfile();
  },

  // 从后端获取用户信息的函数
  async fetchUserProfile() {
    try {
      const res = await requestWithAuth({ url: '/api/profile' });
      this.setData({ userInfo: res });
    } catch (error) {
      wx.showToast({ title: '用户信息加载失败', icon: 'none' });
      console.error("加载用户信息失败", error);
    }
  },

  // 退出登录函数
  logout: function() {
    wx.showModal({
      title: '提示',
      content: '您确定要退出登录吗？',
      success: (res) => {
        // 用户点击了“确定”
        if (res.confirm) {
          console.log('用户点击确定退出');
          // 1. 清除本地存储的token
          wx.removeStorageSync('token');
          // 2. 重启小程序并跳转到登录页
          wx.reLaunch({
            url: '/pages/index/index',
          });
        }
      }
    })
  },

  navigateTo(e) {
    wx.navigateTo({
      url: e.currentTarget.dataset.url
    });
  },
});