import React from 'react';
import Layout from '../components/layout/Layout';

const PrivacyPolicy: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold mb-6">隐私政策</h1>
        
        <div className="bg-white rounded-lg p-6 space-y-4">
          <section>
            <h2 className="text-xl font-semibold mb-3">1. 信息收集</h2>
            <p className="text-gray-700">
              豆粕组合策略分析平台（以下简称"本平台"）尊重并保护用户隐私。我们可能收集以下信息：
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>您提供的账户信息（如用户名、邮箱等）</li>
              <li>交易策略和分析偏好设置</li>
              <li>使用本平台的日志信息</li>
              <li>设备信息和浏览数据</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">2. 信息使用</h2>
            <p className="text-gray-700">我们使用收集的信息用于：</p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>提供、维护和改进我们的服务</li>
              <li>开发新的服务和功能</li>
              <li>个性化您的体验</li>
              <li>分析平台使用情况</li>
              <li>发送服务通知和更新</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">3. 信息共享</h2>
            <p className="text-gray-700">我们不会出售或出租您的个人信息给第三方。在以下情况下，我们可能会分享您的信息：</p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>经您同意</li>
              <li>与提供服务相关的合作伙伴共享（如数据处理服务商）</li>
              <li>遵守法律要求、保护我们的权利或防止滥用</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">4. 数据安全</h2>
            <p className="text-gray-700">
              我们采取合理的技术和组织措施保护您的个人信息，防止未经授权的访问、披露或滥用。然而，没有任何互联网传输或电子存储方法是100%安全的。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">5. Cookie和类似技术</h2>
            <p className="text-gray-700">
              我们使用Cookie和类似技术来记住您的偏好设置、分析使用模式、优化服务体验。您可以通过浏览器设置管理Cookie偏好。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">6. 您的权利</h2>
            <p className="text-gray-700">
              根据适用的数据保护法，您有权访问、更正、删除您的个人信息，并限制或反对其处理。如需行使这些权利，请联系我们。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">7. 隐私政策变更</h2>
            <p className="text-gray-700">
              我们可能会更新本隐私政策以反映服务变化或法律要求。更新后的政策将在本页面公布，重大变更时我们会通知您。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">8. 联系我们</h2>
            <p className="text-gray-700">
              如果您对本隐私政策有任何问题或疑虑，请通过以下方式联系我们：<br />
              邮箱：support@soymeal-strategy.com<br />
              电话：400-123-4567
            </p>
          </section>

          <div className="text-gray-500 text-sm mt-8">
            最后更新日期：2025年3月30日
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default PrivacyPolicy; 