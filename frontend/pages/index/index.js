// pages/index/index.js (最终版，包含所有功能)
Page({
    data: {
      username: '',
      password: '',
      rememberMe: false, // 新增：控制复选框状态
    },
  
    // 页面加载时执行
    onLoad: function (options) {
      // 【修改】自动填充已记住的账号密码
      const savedCredentials = wx.getStorageSync('savedCredentials');
      if (savedCredentials) {
        this.setData({
          username: savedCredentials.username,
          password: savedCredentials.password,
          rememberMe: true,
        });
      }
      // (原有的自动登录逻辑保持不变)
      const token = wx.getStorageSync('token');
      if (token) {
        // ...
      }
    },
    
    // 新增：处理复选框变化的函数
    onRememberMeChange: function(e) {
      this.setData({
        rememberMe: e.detail.value.length > 0
      });
    },
  
    // 【修改】登录函数，增加保存或清除密码的逻辑
    onLoginTap: function() {
      let { username, password, rememberMe } = this.data; // 解构获取数据
      if (username.length === 0 || password.length === 0) { /* ... */ return; }
  
      wx.request({
        url: 'https://beverage-167990-7-1363892886.sh.run.tcloudbase.com/api/login', // 请确保这个地址正确
        method: 'POST',
        data: { username, password },
        success: (res) => {
          if (res.data.code === 200) {
             // 【新增提醒】登录成功
             wx.showToast({
                title: '登录成功!',
                icon: 'success',
                duration: 1500
            });
            wx.setStorageSync('token', res.data.token);
  
            // 【新增逻辑】根据复选框状态决定是否保存密码
            if (rememberMe) {
              wx.setStorageSync('savedCredentials', { username, password });
            } else {
              wx.removeStorageSync('savedCredentials');
            }
  
            // 延迟跳转，让用户能看到提示
            setTimeout(() => {
                wx.switchTab({ url: '/pages/home/home' });
            }, 1500);
          } else {
            // 【新增提醒】登录失败及原因
            let errorMessage = res.data.message || '未知错误';
            wx.showToast({
                title: '登录失败，原因：' + errorMessage,
                icon: 'none',
                duration: 2500 // 延长显示时间以便用户看清原因
            });
          }
        },
        fail: (err) => {
            // 【新增提醒】网络请求失败
            console.error('登录请求失败:', err);
            wx.showToast({
                title: '登录失败，原因：网络错误',
                icon: 'none',
                duration: 2500
            });
        }
      });
    },
  
    // 跳转到注册页
    goToRegister() {
      wx.navigateTo({
        url: '/pages/register/register',
      });
    },
  
    // 原有的 onUsernameInput 和 onPasswordInput 函数保持不变
    onUsernameInput: function(e) { this.setData({ username: e.detail.value }); },
    onPasswordInput: function(e) { this.setData({ password: e.detail.value }); },
  });