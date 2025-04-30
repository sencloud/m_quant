import React from 'react';
import Layout from '../components/layout/Layout';

const TermsOfService: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold mb-6">服务条款</h1>
        
        <div className="bg-white rounded-lg p-6 space-y-4">
          <section>
            <h2 className="text-xl font-semibold mb-3">1. 接受条款</h2>
            <p className="text-gray-700">
              欢迎使用新致量化策略分析平台（以下简称"本平台"或"我们"）。通过访问或使用我们的服务，您同意受本服务条款的约束。如果您不同意这些条款，请勿使用本平台。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">2. 服务说明</h2>
            <p className="text-gray-700">
              本平台提供豆粕市场分析、交易策略推荐、风险管理工具等服务。我们保留随时修改、暂停或终止部分或全部服务的权利，恕不另行通知。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">3. 用户账户</h2>
            <p className="text-gray-700">
              您可能需要创建账户才能使用某些服务功能。您应当：
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>提供准确、完整的注册信息</li>
              <li>保护账户安全，对账户活动负责</li>
              <li>及时更新账户信息</li>
              <li>未经我们事先书面同意，不得转让账户</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">4. 用户行为规范</h2>
            <p className="text-gray-700">
              使用本平台时，您同意不会：
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>违反任何适用法律法规</li>
              <li>侵犯他人知识产权或隐私权</li>
              <li>上传含有病毒、木马等恶意代码的内容</li>
              <li>干扰或破坏平台服务或服务器</li>
              <li>未经授权收集用户信息</li>
              <li>利用本平台进行欺诈活动</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">5. 知识产权</h2>
            <p className="text-gray-700">
              本平台的所有内容，包括但不限于文本、图形、图像、数据、分析模型、软件等，均受知识产权法保护，归本平台或其许可方所有。未经我们明确书面许可，您不得复制、修改、分发、销售或利用这些内容。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">6. 免责声明</h2>
            <p className="text-gray-700">
              本平台提供的所有信息和分析仅供参考，不构成投资建议，不保证准确性、完整性或时效性。用户应当自行承担使用本平台进行投资决策的风险。我们对因使用本平台导致的任何损失不承担责任。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">7. 责任限制</h2>
            <p className="text-gray-700">
              在法律允许的最大范围内，本平台对于因使用或无法使用本服务而导致的任何直接、间接、附带、特殊或后果性损害不承担责任，即使我们已被告知此类损害的可能性。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">8. 修改条款</h2>
            <p className="text-gray-700">
              我们保留随时修改本服务条款的权利。修改后的条款将在本平台上发布。您继续使用本平台将被视为接受修改后的条款。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">9. 终止</h2>
            <p className="text-gray-700">
              我们保留因任何理由随时终止您使用本平台的权利，无需事先通知。一旦终止，您访问本平台的权利将立即停止。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">10. 适用法律</h2>
            <p className="text-gray-700">
              本服务条款受中华人民共和国法律管辖，并按其解释。与本条款相关的任何争议应提交至本平台所在地有管辖权的法院解决。
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

export default TermsOfService; 