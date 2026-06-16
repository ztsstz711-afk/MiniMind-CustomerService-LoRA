"""Build v2 customer-service SFT data with stronger hard cases."""

import json
import random
from collections import Counter
from pathlib import Path


SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "customer_service_sft_v2.jsonl"

CATEGORY_TARGETS = {
    "物流查询": 90,
    "退款进度": 90,
    "退换货申请": 90,
    "发票开具": 90,
    "优惠券使用": 90,
    "商品咨询": 90,
    "订单取消": 90,
    "投诉安抚": 120,
    "拒绝不合理请求": 160,
    "地址修改": 90,
}

INSTRUCTIONS = [
    "你是一名电商平台售后客服，请根据用户问题给出礼貌、合规、可执行的回复。",
    "请作为电商售后客服处理用户诉求，说明规则、必要信息和下一步操作，不作超出规则的承诺。",
    "请生成一条专业客服回复：先安抚用户，再核实信息，并给出符合平台规则的处理建议。",
    "请以电商售后合规客服身份回复用户，遇到不合理或违规请求时要礼貌拒绝并给出替代方案。",
]

OPENINGS = [
    "您好，理解您现在比较着急。",
    "您好，很抱歉这次情况给您带来了不便。",
    "您好，您的问题我已了解，会尽量协助您按规则处理。",
    "您好，先跟您说明一下处理规则，避免后续来回耽误时间。",
]

INFO_REQUESTS = {
    "物流查询": [
        "请提供订单号，并确认收件人姓名或手机号后四位。",
        "请您补充订单号、物流单号以及当前页面显示的物流状态截图。",
        "麻烦提供订单号和收货地址所在城市，方便核对承运方轨迹。",
    ],
    "退款进度": [
        "请提供订单号、退款申请时间和原支付方式。",
        "请补充退款详情页截图、订单号以及支付渠道。",
        "麻烦确认订单号和退款是否为整单退款或部分退款。",
    ],
    "退换货申请": [
        "请提供订单号、签收时间、商品问题照片或视频。",
        "麻烦补充订单号、商品现状、外包装是否完整以及希望退货还是换货。",
        "请上传商品破损或异常位置照片，并说明是否影响正常使用。",
    ],
    "发票开具": [
        "请提供订单号、发票类型、抬头、税号和接收邮箱。",
        "麻烦确认开票主体、发票抬头、税号以及是否需要明细。",
        "请补充订单号和需要修改或补开的具体发票信息。",
    ],
    "优惠券使用": [
        "请提供优惠券名称、有效期、结算商品和不可用提示截图。",
        "麻烦补充订单金额、商品链接、优惠券门槛和页面提示。",
        "请确认优惠券是否已领取到当前账号，并提供结算页截图。",
    ],
    "商品咨询": [
        "请提供商品链接、规格型号和您关注的参数。",
        "麻烦说明使用场景、设备型号或需要确认的服务范围。",
        "请提供商品规格页截图，方便按页面信息核对。",
    ],
    "订单取消": [
        "请提供订单号，并说明需要取消的商品或整单取消。",
        "请确认订单当前状态、是否已发货以及付款方式。",
        "麻烦补充订单号和页面显示的取消提示。",
    ],
    "投诉安抚": [
        "请提供订单号、问题发生时间、相关截图和您希望解决的诉求。",
        "麻烦补充沟通记录、售后单号和目前卡住的环节。",
        "请说明最希望优先解决的问题，我们会按凭证核实。",
    ],
    "拒绝不合理请求": [
        "如果存在真实售后问题，请提供本人订单号、实际问题和有效凭证。",
        "如需正常售后协助，请通过订单所属账号提交真实材料。",
        "为了保障交易安全，请先完成订单身份核验并提供真实问题说明。",
    ],
    "地址修改": [
        "请提供订单号、原收件信息核验项和需要修改的新地址。",
        "麻烦补充订单当前物流状态、新收件地址和联系电话。",
        "请确认订单是否已出库，并提供页面显示的地址修改提示。",
    ],
}

RULES = {
    "物流查询": [
        "物流时效会受揽收、中转、天气和末端派送影响，具体以承运方实时轨迹为准。",
        "异常签收、长时间无更新或退回件需要先由承运方核实，客服不能直接承诺准确送达时间。",
        "同一订单拆包发货时，不同包裹可能有不同物流单号，需要分别核对。",
    ],
    "退款进度": [
        "退款通常按原支付渠道退回，平台处理完成后还会经过支付机构或银行入账。",
        "退货退款需要结合退货物流签收、商家验收和平台审核结果处理。",
        "部分退款、组合支付或信用卡支付的到账时间可能不同，需以退款详情页和支付渠道记录为准。",
    ],
    "退换货申请": [
        "退换货需结合商品类型、签收时间、是否影响二次销售和问题凭证判断。",
        "质量问题通常需要照片、视频或检测信息；非质量问题需按七天无理由及运费规则处理。",
        "生鲜、定制、拆封影响安全或价值的商品，售后规则可能与普通商品不同。",
    ],
    "发票开具": [
        "发票内容、金额和抬头必须与真实交易一致，优惠抵扣部分通常不能虚增开票。",
        "已开具发票如需修改，通常要先按规则作废或红冲后重新开具。",
        "公司抬头发票需要准确税号，发票类型和开票时效以商家及平台规则为准。",
    ],
    "优惠券使用": [
        "优惠券受有效期、适用商品、账号范围、门槛金额和叠加规则限制。",
        "优惠券不能直接折现、提现或绕过活动规则使用。",
        "取消订单或退货后的优惠券退回规则，需以券详情和订单状态为准。",
    ],
    "商品咨询": [
        "商品参数、库存、配件和售后服务以商品详情页及商家确认信息为准。",
        "客服不能对未核实的兼容性、现货或服务范围作绝对承诺。",
        "不同规格、批次或活动套装的配件可能不同，需按具体商品链接核对。",
    ],
    "订单取消": [
        "订单能否取消取决于履约状态；未发货可尝试取消，已发货通常需按拦截、拒收或售后处理。",
        "预售、定制、拼团和组合订单可能有额外取消限制。",
        "取消申请提交后是否成功，以系统审核和商家处理结果为准。",
    ],
    "投诉安抚": [
        "平台会依据订单记录、售后记录、沟通记录和有效凭证核实处理。",
        "处理时效需以实际核查进度为准，客服不能在未核实前承诺具体赔付或结果。",
        "情绪问题会记录并反馈，但最终方案仍需符合平台规则和证据情况。",
    ],
    "拒绝不合理请求": [
        "平台不能协助虚假退款、伪造凭证、虚开发票、泄露隐私或绕过风控规则。",
        "退款、退货、补偿和发票都必须基于真实交易、有效凭证和平台规则处理。",
        "涉及他人信息、商家私人联系方式或后台状态修改的请求，客服不能提供或代为操作。",
    ],
    "地址修改": [
        "地址能否修改取决于订单是否出库和承运方当前状态。",
        "已发货订单通常只能尝试联系承运方改址，是否成功和费用以承运方规则为准。",
        "跨区域、超配送范围或身份核验不通过时，平台无法直接修改地址。",
    ],
}

NEXT_STEPS = {
    "物流查询": [
        "核实后可以先查看最新轨迹；若超过正常时效仍无更新，可提交物流异常核查。",
        "建议您先在订单页查看是否有多个包裹；如确认异常，我们会按流程联系承运方核查。",
        "如果页面显示异常签收，请保留未收到货说明和周边代收点核实结果，后续可发起物流投诉。",
    ],
    "退款进度": [
        "您可以先在退款详情页查看退款流水；若超过提示时效仍未到账，可联系支付渠道核查。",
        "若退货已签收但未退款，请在售后单中补充物流签收凭证，等待商家验收结果。",
        "如页面显示退款失败，可按提示重新提交或联系平台客服核对失败原因。",
    ],
    "退换货申请": [
        "请在订单详情进入售后入口，选择退货或换货并上传凭证，审核结果以页面为准。",
        "如属于运输破损，请保留外包装和面单，按页面要求上传照片后等待核实。",
        "若超过普通售后期但疑似质量问题，可提交质量问题凭证申请进一步核查。",
    ],
    "发票开具": [
        "您可以在订单详情的发票入口提交或修改信息，开具进度以页面展示为准。",
        "如已开票需更正，请先在发票详情页查看是否支持作废或红冲后重开。",
        "如果入口不可用，可提供订单信息，由平台协助核实商家开票规则。",
    ],
    "优惠券使用": [
        "建议先查看券详情的适用范围和门槛；条件满足仍不可用时，请保留结算页截图提交核查。",
        "如订单取消后券未退回，请查看券状态和退回规则，必要时提交订单号核实。",
        "若活动规则不支持叠加或指定商品不可用，只能按页面规则重新选择商品或优惠方式。",
    ],
    "商品咨询": [
        "建议您以商品详情页参数为准；如仍不确定，可提供使用场景后由商家进一步确认。",
        "如涉及兼容性，请先核对型号、接口和系统版本，避免下单后无法使用。",
        "若需要售后服务范围，请查看商品页服务说明或提供地址后核对覆盖情况。",
    ],
    "订单取消": [
        "未发货时可在订单详情提交取消申请；已发货时建议查看是否支持拦截或拒收。",
        "如果页面显示审核中，请等待商家处理，结果以系统通知为准。",
        "若只取消部分商品，请在订单详情查看是否支持拆单取消，不支持时需按整单规则处理。",
    ],
    "投诉安抚": [
        "我们会先记录您的诉求，并建议您通过订单投诉入口上传凭证，便于平台复核。",
        "请您保留沟通记录和问题截图，平台会按售后流程核实并反馈进展。",
        "如果此前处理结果您不认可，可以提交复核申请，说明争议点和期望方案。",
    ],
    "拒绝不合理请求": [
        "我们可以继续协助您处理真实售后问题，但不能按虚假理由或绕过平台规则操作。",
        "建议您通过订单售后入口提交真实凭证，平台会在合规范围内核实可处理方案。",
        "如您对规则有疑问，可以提供订单号，我们会帮您核对当前可用的合规处理入口。",
    ],
    "地址修改": [
        "未出库时可在订单详情尝试修改；已发货时可联系承运方尝试改址。",
        "如果无法修改，建议关注物流派送电话，必要时与快递员协商自提或拒收后重拍。",
        "若新地址超出配送范围，可能无法变更，只能按订单状态选择取消、拒收或售后。",
    ],
}

SCENARIOS = {
    "物流查询": [
        ("我的订单物流四天没更新，是不是丢件了？", "medium", ["logistics", "delay", "order_id_required"]),
        ("快递显示已签收，但我本人没收到。", "hard", ["logistics", "signed_not_received", "proof_required"]),
        ("包裹一直显示揽收，商家是不是虚假发货？", "hard", ["logistics", "pickup_delay", "appeasement"]),
        ("一个订单买了三件，只收到一件，剩下的在哪里？", "medium", ["logistics", "split_package", "order_id_required"]),
        ("物流显示退回商家，我还想要这个商品怎么办？", "medium", ["logistics", "returned", "next_step"]),
        ("预计昨天送达，现在还没到，今天能保证送到吗？", "hard", ["logistics", "no_overpromise", "delivery_eta"]),
        ("快递送错小区了，你们马上给我找回来。", "hard", ["logistics", "wrong_address", "carrier_check"]),
        ("物流轨迹显示异常中转，我应该等还是申请退款？", "medium", ["logistics", "refund_boundary", "next_step"]),
        ("同城订单为什么配送这么慢？", "easy", ["logistics", "delay", "policy"]),
        ("快递员联系不上，我的件会不会被退回？", "medium", ["logistics", "delivery_failed", "carrier_check"]),
    ],
    "退款进度": [
        ("退款审核通过三天了，钱为什么还没到账？", "medium", ["refund", "payment_channel", "order_id_required"]),
        ("退货物流显示签收，但退款一直处理中。", "medium", ["refund", "return_received", "merchant_check"]),
        ("我只收到一半退款，剩下的钱去哪了？", "hard", ["refund", "partial_refund", "payment_channel"]),
        ("信用卡支付退款是不是要等很久？", "easy", ["refund", "credit_card", "policy"]),
        ("退款失败了，页面让我重新申请，怎么处理？", "medium", ["refund", "failed", "next_step"]),
        ("我取消订单后优惠也没退，退款金额不对。", "hard", ["refund", "coupon", "amount_dispute"]),
        ("平台说退了但银行卡没记录，是不是骗我？", "hard", ["refund", "complaint", "payment_channel"]),
        ("售后单关闭了但我没收到退款。", "hard", ["refund", "closed_case", "proof_required"]),
        ("微信退款在哪里看流水号？", "easy", ["refund", "wechat", "next_step"]),
        ("退款能不能退到另一个人的账户？", "hard", ["refund", "invalid_request", "account_security"]),
    ],
    "退换货申请": [
        ("衣服尺码不合适，吊牌还在可以换吗？", "easy", ["return_exchange", "size", "policy"]),
        ("收到商品破损，我要退货并要求运费险赔付。", "medium", ["return_exchange", "damaged", "proof_required"]),
        ("商品拆封用了两天不喜欢，还能七天无理由吗？", "hard", ["return_exchange", "used_item", "boundary"]),
        ("超过七天才发现质量问题，还能售后吗？", "hard", ["return_exchange", "after_sale_period", "quality"]),
        ("退货包装盒丢了，但商品没用过。", "medium", ["return_exchange", "package_missing", "policy"]),
        ("赠品被我用了，主商品可以退吗？", "hard", ["return_exchange", "gift", "boundary"]),
        ("生鲜收到不新鲜，拍照后怎么处理？", "medium", ["return_exchange", "fresh_food", "proof_required"]),
        ("换货后还是有问题，可以再换一次吗？", "medium", ["return_exchange", "repeat_issue", "next_step"]),
        ("商家拒绝我的退货申请，我想申诉。", "hard", ["return_exchange", "appeal", "proof_required"]),
        ("商品影响二次销售但我坚持无理由退货。", "hard", ["return_exchange", "invalid_request", "policy"]),
    ],
    "发票开具": [
        ("订单完成后还能补开公司抬头发票吗？", "easy", ["invoice", "company_title", "tax_id"]),
        ("发票抬头写错了，可以重新开吗？", "medium", ["invoice", "correction", "red_flush"]),
        ("优惠券抵扣的金额也帮我开进发票里。", "hard", ["invoice", "coupon", "invalid_request"]),
        ("我想把 200 元订单开成 500 元发票。", "hard", ["invoice", "over_invoice", "polite_refusal"]),
        ("多个订单能合并开一张发票吗？", "medium", ["invoice", "merge", "policy"]),
        ("纸质发票寄丢了，能补寄吗？", "medium", ["invoice", "paper_invoice", "next_step"]),
        ("电子发票下载链接过期了怎么办？", "easy", ["invoice", "download", "next_step"]),
        ("赠品能不能开在发票明细里？", "hard", ["invoice", "gift", "policy"]),
        ("我没有税号，能开公司发票吗？", "medium", ["invoice", "tax_id", "boundary"]),
        ("已经退款的订单还能开发票吗？", "hard", ["invoice", "refunded_order", "policy"]),
    ],
    "优惠券使用": [
        ("优惠券还没过期但结算时不可用。", "medium", ["coupon", "checkout", "screenshot_required"]),
        ("优惠券昨天过期了，能帮我恢复吗？", "hard", ["coupon", "expired", "polite_refusal"]),
        ("两张优惠券为什么不能一起用？", "easy", ["coupon", "stacking", "policy"]),
        ("取消订单后优惠券没有退回来。", "medium", ["coupon", "cancel_order", "next_step"]),
        ("新人券领取了但账户里找不到。", "medium", ["coupon", "new_user", "account_check"]),
        ("优惠券能不能提现到微信？", "hard", ["coupon", "cash_out", "polite_refusal"]),
        ("满减门槛到了还是提示金额不足。", "medium", ["coupon", "threshold", "screenshot_required"]),
        ("退货后优惠券还能恢复吗？", "hard", ["coupon", "return", "boundary"]),
        ("活动商品说参加满减，结算却不显示。", "medium", ["coupon", "campaign", "screenshot_required"]),
        ("你直接给我补一张无门槛券吧。", "hard", ["coupon", "compensation", "policy"]),
    ],
    "商品咨询": [
        ("这款手机是全新未拆封吗？", "easy", ["product", "new_item", "merchant_confirm"]),
        ("衣服尺码偏大还是偏小？", "easy", ["product", "size", "recommendation"]),
        ("这款电器支持全国联保吗？", "medium", ["product", "warranty", "service"]),
        ("包装里有哪些配件？", "easy", ["product", "accessories", "detail_page"]),
        ("食品生产日期能保证是本月的吗？", "medium", ["product", "freshness", "no_overpromise"]),
        ("这个型号和我的设备兼容吗？", "medium", ["product", "compatibility", "info_required"]),
        ("图片颜色和实物会不会有色差？", "easy", ["product", "color_difference", "policy"]),
        ("你能保证今天下单明天一定到吗？", "hard", ["product", "delivery_promise", "no_overpromise"]),
        ("库存只剩一件，你能帮我私下留货吗？", "hard", ["product", "invalid_request", "policy"]),
        ("商品详情页没写防水，我能当防水用吗？", "hard", ["product", "safety", "no_overpromise"]),
    ],
    "订单取消": [
        ("刚付款买错型号，还没发货可以取消吗？", "easy", ["cancel_order", "not_shipped", "next_step"]),
        ("订单已发货，我不想要了能取消吗？", "medium", ["cancel_order", "shipped", "boundary"]),
        ("预售商品尾款付了还能取消吗？", "hard", ["cancel_order", "presale", "policy"]),
        ("拼团订单可以中途取消吗？", "medium", ["cancel_order", "group_buy", "policy"]),
        ("订单里三件商品能只取消一件吗？", "medium", ["cancel_order", "partial_cancel", "boundary"]),
        ("取消申请一直审核中，你能直接通过吗？", "hard", ["cancel_order", "invalid_request", "no_overpromise"]),
        ("礼品卡支付的订单取消后钱怎么退？", "medium", ["cancel_order", "gift_card", "refund"]),
        ("商家超时未发货，我要取消并赔偿。", "hard", ["cancel_order", "late_shipping", "compensation"]),
        ("我提交取消后又不想取消了，能撤回吗？", "easy", ["cancel_order", "withdraw", "next_step"]),
        ("定制商品还没生产，能不能取消？", "hard", ["cancel_order", "customized", "policy"]),
    ],
    "投诉安抚": [
        ("我已经催了五次，你们到底管不管？", "hard", ["complaint", "appeasement", "urgent"]),
        ("客服一直复制粘贴，我要投诉你们。", "hard", ["complaint", "service_quality", "appeasement"]),
        ("退款拖这么久，你们是不是故意骗我？", "hard", ["complaint", "refund", "trust_issue"]),
        ("再不处理我就去平台投诉并差评。", "hard", ["complaint", "threat", "next_step"]),
        ("我不相信你们客服了，给我明确时限。", "hard", ["complaint", "trust_issue", "time_limit"]),
        ("商品质量太差，我很生气。", "medium", ["complaint", "quality", "appeasement"]),
        ("快递员态度恶劣，你们必须给说法。", "hard", ["complaint", "courier", "evidence"]),
        ("售后结果不公平，我要求重新审核。", "hard", ["complaint", "appeal", "review"]),
        ("活动规则写得不清楚，害我多花钱。", "medium", ["complaint", "campaign", "appeasement"]),
        ("商家一直拖延发货，我已经无法接受。", "hard", ["complaint", "late_shipping", "time_limit"]),
        ("收到脏污商品，我觉得被欺骗了。", "hard", ["complaint", "damaged", "trust_issue"]),
        ("你们说会回复，但一直没人联系我。", "hard", ["complaint", "follow_up", "time_limit"]),
        ("同一个问题解释三遍都没解决。", "hard", ["complaint", "repeated_contact", "appeasement"]),
        ("我要主管立刻给我打电话。", "hard", ["complaint", "escalation", "privacy"]),
        ("不赔偿我就曝光你们。", "hard", ["complaint", "threat", "compensation_boundary"]),
    ],
    "拒绝不合理请求": [
        ("优惠券过期了，你后台帮我恢复一下。", "hard", ["invalid_request", "coupon", "polite_refusal"]),
        ("把 100 元订单开成 1000 元发票给我报销。", "hard", ["invalid_request", "invoice", "polite_refusal"]),
        ("货我不退了，你直接给我退款。", "hard", ["invalid_request", "refund", "polite_refusal"]),
        ("商品我用了一个月，按全新给我退。", "hard", ["invalid_request", "used_item", "policy"]),
        ("把别人的订单信息发我看看价格。", "hard", ["invalid_request", "privacy", "polite_refusal"]),
        ("给我商家的私人手机号，我自己找他。", "hard", ["invalid_request", "privacy", "merchant_contact"]),
        ("超过售后期了，你强制给我退货。", "hard", ["invalid_request", "after_sale_period", "policy"]),
        ("不给我赔偿我就差评，你看着办。", "hard", ["invalid_request", "threat", "compensation_boundary"]),
        ("帮我伪造物流状态，证明我没收到。", "hard", ["invalid_request", "logistics_fraud", "polite_refusal"]),
        ("你绕过平台规则，直接改成退款成功。", "hard", ["invalid_request", "bypass_policy", "polite_refusal"]),
        ("我没下单也想申请仅退款。", "hard", ["invalid_request", "refund", "identity_check"]),
        ("不用验证身份，把退款打到我朋友账户。", "hard", ["invalid_request", "account_security", "polite_refusal"]),
        ("帮我把普通会员改成最高等级。", "hard", ["invalid_request", "account", "bypass_policy"]),
        ("商品没问题，你帮我写质量问题理由。", "hard", ["invalid_request", "fake_reason", "polite_refusal"]),
        ("我要重复申请退款，多退一笔。", "hard", ["invalid_request", "duplicate_refund", "polite_refusal"]),
        ("给我内部客服账号，我自己改订单。", "hard", ["invalid_request", "security", "polite_refusal"]),
        ("把商家的保证金信息发给我。", "hard", ["invalid_request", "privacy", "merchant_info"]),
        ("我想用别人的优惠券，你帮我转过来。", "hard", ["invalid_request", "coupon", "account_security"]),
        ("帮我删除不利的售后记录。", "hard", ["invalid_request", "record_tamper", "polite_refusal"]),
        ("你承认是平台全责并保证赔十倍。", "hard", ["invalid_request", "overpromise", "compensation_boundary"]),
    ],
    "地址修改": [
        ("订单刚付款，能改收货地址吗？", "easy", ["address", "not_shipped", "next_step"]),
        ("已经发货但地址填错了怎么办？", "medium", ["address", "shipped", "carrier_check"]),
        ("我只想改手机号，不改地址。", "easy", ["address", "phone", "identity_check"]),
        ("一个订单能拆成两个地址吗？", "medium", ["address", "split_delivery", "policy"]),
        ("预售订单发货前能修改地址吗？", "easy", ["address", "presale", "next_step"]),
        ("新地址不在配送范围内怎么办？", "hard", ["address", "out_of_range", "policy"]),
        ("修改地址会不会影响送达时间？", "medium", ["address", "delivery_eta", "no_overpromise"]),
        ("省份填错了，能直接帮我改吗？", "medium", ["address", "province", "identity_check"]),
        ("快递正在派送，能改送公司吗？", "hard", ["address", "delivering", "carrier_check"]),
        ("页面没有修改地址入口，是不是不能改？", "medium", ["address", "no_entry", "next_step"]),
    ],
}


def difficulty_for(category, base_difficulty, variant):
    if category in {"拒绝不合理请求", "投诉安抚"}:
        return "hard" if variant < 7 else base_difficulty
    if base_difficulty == "hard":
        return "hard"
    if variant % 5 == 0:
        return "medium"
    return base_difficulty


def response_for(category, scenario, difficulty, tags, variant):
    opening = random.choice(OPENINGS)
    rule = random.choice(RULES[category])
    info = random.choice(INFO_REQUESTS[category])
    next_step = random.choice(NEXT_STEPS[category])

    if category == "拒绝不合理请求":
        refusal = random.choice([
            "这类操作不符合平台规则，我无法为您办理。",
            "很抱歉，涉及虚假凭证、隐私信息或绕过规则的请求不能支持。",
            "该请求存在交易安全或合规风险，客服不能协助操作。",
            "为了保障买卖双方权益，我们不能按不真实信息处理售后。",
        ])
        alternatives = random.choice([
            "如果确实存在商品、物流或服务问题，我们可以按真实凭证为您核实售后方案。",
            "建议您通过订单售后入口提交真实问题和凭证，平台会按规则审核。",
            "您可以提供本人订单号和实际情况，我们会帮您确认当前可用的合规处理方式。",
        ])
        templates = [
            f"{opening}{refusal}{rule}{info}{alternatives}",
            f"{opening}{rule}{refusal}{alternatives}{info}",
            f"{opening}{refusal}但如果您有真实售后诉求，{info}{next_step}",
            f"{opening}{refusal}我们可以继续协助合规售后：{info}{next_step}",
        ]
        return templates[variant % len(templates)]

    if category == "投诉安抚":
        appease = random.choice([
            "您的不满我能理解，我们会先把问题和诉求记录清楚。",
            "这次处理体验确实不理想，先向您表示抱歉。",
            "很抱歉让您多次反馈仍未解决，我理解这确实会让人着急，我们会按凭证继续核实。",
            "我理解您希望尽快得到明确回复，但处理结果需要以核实情况为准。",
        ])
        templates = [
            f"{opening}{appease}{rule}{info}{next_step}",
            f"{opening}{appease}为避免遗漏，{info}{rule}{next_step}",
            f"{opening}{rule}{appease}{info}{next_step}",
            f"{opening}{appease}暂时不能在未核实前承诺赔付或固定结果。{info}{next_step}",
        ]
        return templates[variant % len(templates)]

    templates = [
        f"{opening}{rule}{info}{next_step}",
        f"{opening}为了准确处理，{info}{rule}{next_step}",
        f"{opening}{rule}建议您先准备相关信息：{info.removeprefix('请')}{next_step}",
        f"{opening}这个问题需要结合订单状态判断。{rule}{info}{next_step}",
        f"{opening}我先说明规则边界：{rule}目前建议您这样操作：{info}{next_step}",
    ]
    return templates[variant % len(templates)]


def build_samples():
    random.seed(SEED)
    samples = []
    seen_pairs = set()

    for category, target in CATEGORY_TARGETS.items():
        scenarios = SCENARIOS[category]
        per_scenario = target // len(scenarios)
        extra = target % len(scenarios)

        for scenario_index, (question, base_difficulty, base_tags) in enumerate(scenarios):
            variants = per_scenario + (1 if scenario_index < extra else 0)
            for variant in range(variants):
                difficulty = difficulty_for(category, base_difficulty, variant)
                output = response_for(category, question, difficulty, base_tags, variant)
                pair = (question, output)
                if pair in seen_pairs:
                    output = f"{output} 如页面提示与上述不一致，请以订单详情页的最新提示为准。"
                    pair = (question, output)
                seen_pairs.add(pair)

                tags = list(dict.fromkeys(base_tags + [
                    "policy",
                    "next_step",
                    "order_id_required" if category not in {"商品咨询"} else "info_required",
                ]))
                samples.append({
                    "instruction": random.choice(INSTRUCTIONS),
                    "input": question,
                    "output": output,
                    "category": category,
                    "difficulty": difficulty,
                    "tags": tags,
                })

    random.shuffle(samples)
    return samples


def main():
    samples = build_samples()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for sample in samples:
            file.write(json.dumps(sample, ensure_ascii=False) + "\n")

    counts = Counter(sample["category"] for sample in samples)
    print(f"Generated samples: {len(samples)}")
    print(f"Output path: {OUTPUT_PATH}")
    print(f"Category counts: {dict(sorted(counts.items()))}")


if __name__ == "__main__":
    main()
