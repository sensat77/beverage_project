import { requestWithAuth } from '../../utils/api.js';

Page({
  data: {
    old_password: '',
    new_password: '',
    confirm_password: ''
  },
  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value });
  },
  async onSubmit() {
    if (this.data.new_password !== this.data.confirm_password) {
      wx.showToast({ title: '两次输入的新密码不一致', icon: 'none' });
      return;
    }
    try {
      await requestWithAuth({
        url: '/api/change-password',
        method: 'POST',
        data: {
          old_password: this.data.old_password,
          new_password: this.data.new_password
        }
      });
      wx.showToast({ title: '修改成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1500);
    } catch (error) {
      wx.showToast({ title: error.message || '修改失败', icon: 'none' });
    }
  }
})