import React from 'react';
import Layout from '../components/layout/Layout';

const Disclaimer: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-2xl font-bold mb-6">免责声明</h1>
        
        <div className="bg-white rounded-lg p-6 space-y-4">
          <section>
            <h2 className="text-xl font-semibold mb-3">1. 信息用途</h2>
            <p className="text-gray-700">
              豆粕组合策略分析平台（以下简称"本平台"）提供的所有信息、分析、策略建议和其他内容仅供参考，不构成投资建议或交易指导。用户在做出任何投资决策前，应当咨询专业金融顾问。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">2. 风险提示</h2>
            <p className="text-gray-700">
              股票、期货、基金和衍生品交易涉及重大风险，可能导致严重的财务损失。本平台提供的策略和分析不保证能获得投资收益或避免损失。用户在交易前应充分了解相关风险，并根据自身财务状况和风险承受能力作出决策。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">3. 内容准确性</h2>
            <p className="text-gray-700">
              尽管我们努力确保本平台提供的信息准确可靠，但我们不对信息的准确性、完整性、时效性或适用性做出任何保证。市场情况瞬息万变，任何分析和预测可能会因诸多因素而失效。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">4. 技术风险</h2>
            <p className="text-gray-700">
              使用本平台涉及互联网和电子系统的使用，可能会受到硬件故障、软件问题、连接中断、系统延迟等技术因素的影响。用户应当意识到这些风险，并准备好应对可能出现的问题。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">5. 第三方内容</h2>
            <p className="text-gray-700">
              本平台可能包含来自第三方的内容或链接到第三方网站。我们不对这些第三方内容的准确性或可靠性负责，也不对用户访问这些链接可能造成的任何损失或损害承担责任。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">6. 模型和算法局限性</h2>
            <p className="text-gray-700">
              本平台使用的分析模型和算法基于历史数据和特定假设，存在固有局限性。市场行为可能会偏离历史模式，导致模型预测失效。用户不应完全依赖这些模型做出决策。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">7. 责任限制</h2>
            <p className="text-gray-700">
              在法律允许的最大范围内，本平台及其运营者、员工、合作伙伴不对用户因使用或依赖本平台提供的信息而产生的任何直接、间接、附带、特殊或后果性损害承担责任，包括但不限于财务损失、利润损失、业务中断等。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">8. 合规责任</h2>
            <p className="text-gray-700">
              用户应当了解并遵守与股票、期货、基金和衍生品交易相关的所有适用法律、法规和监管要求。本平台不对用户的交易行为是否符合相关法律法规负责，用户应自行承担合规责任。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">9. 资格要求</h2>
            <p className="text-gray-700">
              用户确认其具备使用本平台服务和进行相关交易的法律资格，包括但不限于达到法定年龄、具备足够的风险识别和承担能力等。
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">10. 同意条款</h2>
            <p className="text-gray-700">
              使用本平台即表示您已阅读、理解并接受本免责声明的所有条款。如果您不同意这些条款，请勿使用本平台及其提供的服务。
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

export default Disclaimer; 