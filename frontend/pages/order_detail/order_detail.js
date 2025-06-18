// pages/order_detail/order_detail.js (最终修正版)
import { requestWithAuth } from '../../utils/api.js';

Page({
  data: {
    orderDetail: null,
    isLoading: true
  },

  onLoad: function (options) {
    const orderId = options.id;
    if (orderId) {
      this.fetchOrderDetail(orderId);
    } else {
      wx.showToast({ title: '订单ID缺失', icon: 'none' });
      this.setData({ isLoading: false });
    }
  },

  async fetchOrderDetail(id) {
    this.setData({ isLoading: true });
    try {
      const res = await requestWithAuth({ url: `/api/order/${id}` });

      // 【修正点】对所有需要在界面上显示的小数进行预格式化
      if (res) {
        // 1. 格式化产品列表中的金额
        if (res.items) {
          res.items.forEach(item => {
            item.actual_unit_price_str = (item.actual_unit_price || 0).toFixed(2);
            item.item_commission_str = (item.item_commission || 0).toFixed(2);
          });
        }
        // 2. 格式化总计区的金额
        res.total_commission_str = (res.total_commission || 0).toFixed(2);
        res.display_fee_str = (res.display_fee || 0).toFixed(2);
        res.old_goods_disposal_fee_str = (res.old_goods_disposal_fee || 0).toFixed(2);
        res.gifting_cost_str = (res.gifting_cost || 0).toFixed(2);
      }

      this.setData({ orderDetail: res });

    } catch (error) {
      console.error("加载订单详情失败", error);
      wx.showToast({ title: '加载订单详情失败', icon: 'none' });
    } finally {
      this.setData({ isLoading: false });
    }
  } // <-- 我在这里确保了所有函数之间都有正确的逗号（或在末尾省略）
});