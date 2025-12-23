<template>
	<div class="mt-7 mb-10">
		<!-- Referral Link Section -->
		<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
			{{ __('Your Referral Link') }}
		</h2>
		<div v-if="referralStats.loading" class="text-ink-gray-5 text-sm">
			{{ __('Loading...') }}
		</div>
		<div v-else-if="stats.referral_code">
			<div class="flex items-center gap-3 mb-4">
				<div class="flex-1 bg-surface-gray-2 rounded px-3 py-2 text-sm font-mono text-ink-gray-7 break-all">
					{{ referralLink }}
				</div>
				<Button variant="solid" @click="copyReferralLink">
					<template #prefix>
						<Copy class="w-4 h-4" />
					</template>
					{{ copied ? __('Copied!') : __('Copy Link') }}
				</Button>
			</div>
			<div class="text-sm text-ink-gray-5 mb-4">
				{{ __('Your Code:') }} <span class="font-semibold text-ink-gray-9">{{ stats.referral_code }}</span>
			</div>
		</div>
		<div v-else class="text-ink-gray-7 text-sm italic">
			{{ __('Referral code not available') }}
		</div>

		<!-- Earnings Summary -->
		<div class="mt-7 mb-10">
			<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
				{{ __('Earnings Summary') }}
			</h2>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
				<div class="bg-surface-gray-2 rounded-lg p-4">
					<div class="text-2xl font-semibold text-ink-gray-9">
						{{ stats.total_referrals || 0 }}
					</div>
					<div class="text-sm text-ink-gray-5">
						{{ __('Friends Joined') }}
					</div>
				</div>
				<div class="bg-surface-gray-2 rounded-lg p-4">
					<div class="text-2xl font-semibold text-ink-gray-9">
						{{ formatCurrency(stats.total_earnings) }}
					</div>
					<div class="text-sm text-ink-gray-5">
						{{ __('Total Earnings') }}
					</div>
				</div>
				<div class="bg-surface-gray-2 rounded-lg p-4">
					<div class="text-2xl font-semibold text-ink-gray-9">
						{{ formatCurrency(stats.pending_payout) }}
					</div>
					<div class="text-sm text-ink-gray-5">
						{{ __('Pending Payout') }}
					</div>
				</div>
				<div class="bg-surface-gray-2 rounded-lg p-4">
					<div class="text-2xl font-semibold text-ink-gray-9">
						{{ formatCurrency(stats.paid_payout) }}
					</div>
					<div class="text-sm text-ink-gray-5">
						{{ __('Paid Out') }}
					</div>
				</div>
			</div>
		</div>

		<!-- Payout Method Section -->
		<div class="mt-7 mb-10">
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-lg font-semibold text-ink-gray-9">
					<Wallet class="w-5 h-5 inline-block mr-2" />
					{{ __('Payout Method') }}
				</h2>
				<Button
					v-if="hasPayoutMethod && !isEditing"
					variant="ghost"
					@click="isEditing = true"
					class="text-ink-gray-7"
				>
					<template #prefix>
						<Pencil class="w-3.5 h-3.5" />
					</template>
					{{ __('Edit') }}
				</Button>
			</div>

			<!-- View Mode (Display Card) -->
			<div v-if="hasPayoutMethod && !isEditing" class="bg-surface-gray-2 rounded-lg p-5 border border-outline-gray-1">
				<div class="flex items-center justify-between gap-2">
					<div class="flex items-center gap-4 min-w-0">
						<div class="w-12 h-12 bg-white rounded-full flex-shrink-0 flex items-center justify-center border border-outline-gray-2 shadow-sm">
							<component :is="isBankTransfer ? Library : Smartphone" class="w-5 h-5 text-ink-gray-7" />
						</div>
						<div class="min-w-0">
							<div class="text-sm font-semibold text-ink-gray-9 truncate">
								{{ payoutForm.payout_method }}
								<span v-if="isBankTransfer" class="ml-1 text-ink-gray-5 font-normal">
									({{ payoutForm.payout_bank }})
								</span>
							</div>
							<div class="text-sm text-ink-gray-7 mt-0.5 truncate">
								<span v-if="isEWallet">{{ payoutForm.payout_phone }}</span>
								<span v-else-if="isBankTransfer">
									{{ payoutForm.payout_account_number }}
								</span>
							</div>
							<div v-if="isBankTransfer" class="text-xs text-ink-gray-5 mt-0.5 truncate">
								{{ payoutForm.payout_account_name }}
							</div>
						</div>
					</div>
					<Badge theme="green" variant="subtle" size="sm" class="flex-shrink-0">
						{{ __('Active') }}
					</Badge>
				</div>
			</div>

			<!-- Edit Mode (Form) -->
			<div v-else class="bg-surface-gray-2 rounded-lg p-5 border border-outline-gray-1">
				<div class="grid gap-4">
					<div v-if="isEditing" class="flex justify-end -mb-2">
						<button @click="isEditing = false" class="text-xs text-ink-gray-5 hover:text-ink-gray-8 underline">
							{{ __('Cancel') }}
						</button>
					</div>

					<!-- Payout Method Select -->
					<div>
						<label class="block text-sm font-medium text-ink-gray-7 mb-1">
							{{ __('Payment Method') }}
						</label>
						<select
							v-model="payoutForm.payout_method"
							class="w-full border border-outline-gray-2 rounded-md px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						>
							<option value="">{{ __('Select method...') }}</option>
							<option value="GoPay">GoPay</option>
							<option value="Dana">Dana</option>
							<option value="ShopeePay">ShopeePay</option>
							<option value="OVO">OVO</option>
							<option value="Bank Transfer">Bank Transfer</option>
						</select>
					</div>

					<!-- E-Wallet Phone (shown for e-wallets) -->
					<div v-if="isEWallet">
						<label class="block text-sm font-medium text-ink-gray-7 mb-1">
							{{ __('E-Wallet Phone Number') }}
						</label>
						<input
							v-model="payoutForm.payout_phone"
							type="tel"
							placeholder="08123456789"
							class="w-full border border-outline-gray-2 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
						<p class="text-xs text-ink-gray-5 mt-1">
							{{ __('Phone number registered with your e-wallet') }}
						</p>
					</div>

					<!-- Bank Fields (shown for Bank Transfer) -->
					<div v-if="isBankTransfer">
						<label class="block text-sm font-medium text-ink-gray-7 mb-1">
							{{ __('Bank Name') }}
						</label>
						<select
							v-model="payoutForm.payout_bank"
							class="w-full border border-outline-gray-2 rounded-md px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						>
							<option value="">{{ __('Select bank...') }}</option>
							<option value="BCA">BCA</option>
							<option value="Mandiri">Bank Mandiri</option>
							<option value="BRI">BRI</option>
							<option value="BNI">BNI</option>
							<option value="Aladin">Bank Aladin</option>
						</select>
					</div>

					<div v-if="isBankTransfer">
						<label class="block text-sm font-medium text-ink-gray-7 mb-1">
							{{ __('Account Number') }}
						</label>
						<input
							v-model="payoutForm.payout_account_number"
							type="text"
							placeholder="1234567890"
							class="w-full border border-outline-gray-2 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>

					<div v-if="isBankTransfer">
						<label class="block text-sm font-medium text-ink-gray-7 mb-1">
							{{ __('Account Holder Name') }}
						</label>
						<input
							v-model="payoutForm.payout_account_name"
							type="text"
							placeholder="John Doe"
							class="w-full border border-outline-gray-2 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
						<p class="text-xs text-ink-gray-5 mt-1">
							{{ __('Name as registered with the bank') }}
						</p>
					</div>

					<!-- Save Button -->
					<div class="pt-2">
						<Button
							variant="solid"
							@click="savePayoutInfo"
							:loading="updatePayout?.loading"
							:disabled="!payoutForm.payout_method"
						>
							<template #prefix>
								<Save class="w-4 h-4" />
							</template>
							{{ __('Save Payout Info') }}
						</Button>
						<span v-if="payoutSaved" class="ml-3 text-sm text-green-600 font-medium">
							✓ {{ __('Saved Successfully!') }}
						</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Commission History -->
		<div class="mt-7 mb-10" v-if="commissions.data?.length">
			<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
				{{ __('Commission History') }}
			</h2>
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-outline-gray-2">
							<th class="text-left py-2 px-3 text-ink-gray-5 font-medium">{{ __('Date') }}</th>
							<th class="text-left py-2 px-3 text-ink-gray-5 font-medium">{{ __('Student') }}</th>
							<th class="text-right py-2 px-3 text-ink-gray-5 font-medium">{{ __('Commission') }}</th>
							<th class="text-center py-2 px-3 text-ink-gray-5 font-medium">{{ __('Status') }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="c in commissions.data" :key="c.name" class="border-b border-outline-gray-1">
							<td class="py-2 px-3 text-ink-gray-7">
								{{ dayjs(c.creation).format('DD MMM YYYY') }}
							</td>
							<td class="py-2 px-3 text-ink-gray-9">
								{{ c.referred_student }}
							</td>
							<td class="py-2 px-3 text-right text-ink-gray-9 font-medium">
								{{ formatCurrency(c.commission_amount) }}
							</td>
							<td class="py-2 px-3 text-center">
								<Badge
									:theme="c.payout_status === 'Paid' ? 'green' : 'orange'"
									variant="subtle"
									size="sm"
								>
									{{ c.payout_status }}
								</Badge>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		<div v-else class="mt-7 mb-10">
			<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
				{{ __('Commission History') }}
			</h2>
			<div class="text-ink-gray-7 text-sm italic">
				{{ __('No commissions yet') }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject, reactive } from 'vue'
import { createResource, Button, Badge } from 'frappe-ui'
import { Copy, Wallet, Save, Smartphone, Library, Pencil } from 'lucide-vue-next'

const dayjs = inject('$dayjs')
const copied = ref(false)
const payoutSaved = ref(false)
const isEditing = ref(false)

const props = defineProps({
	profile: {
		type: Object,
		required: true,
	},
})

// Payout form data
const payoutForm = reactive({
	payout_method: '',
	payout_phone: '',
	payout_bank: '',
	payout_account_number: '',
	payout_account_name: '',
})

// Computed helpers for showing/hiding fields
const isEWallet = computed(() => {
	return ['GoPay', 'Dana', 'ShopeePay', 'OVO'].includes(payoutForm.payout_method)
})

const isBankTransfer = computed(() => {
	return payoutForm.payout_method === 'Bank Transfer'
})

const hasPayoutMethod = computed(() => {
	return !!payoutForm.payout_method
})

// Get referral stats
const referralStats = createResource({
	url: 'lms.lms.api.get_referral_stats',
	auto: true,
})

const stats = computed(() => referralStats.data || {})

// Get commission history
const commissions = createResource({
	url: 'lms.lms.api.get_referral_commissions',
	params: {
		limit: 50
	},
	auto: true,
})

// Get payout info
const payoutInfo = createResource({
	url: 'lms.lms.api.get_payout_info',
	auto: true,
	onSuccess(data) {
		// Populate form with existing data
		payoutForm.payout_method = data.payout_method || ''
		payoutForm.payout_phone = data.payout_phone || ''
		payoutForm.payout_bank = data.payout_bank || ''
		payoutForm.payout_account_number = data.payout_account_number || ''
		payoutForm.payout_account_name = data.payout_account_name || ''

		// Set editing to false if data exists, true if new
		isEditing.value = !data.payout_method
	}
})

// Update payout info resource
const updatePayout = createResource({
	url: 'lms.lms.api.update_payout_info',
})

// Save payout info
const savePayoutInfo = async () => {
	try {
		await updatePayout.submit({
			payout_method: payoutForm.payout_method,
			payout_phone: payoutForm.payout_phone,
			payout_bank: payoutForm.payout_bank,
			payout_account_number: payoutForm.payout_account_number,
			payout_account_name: payoutForm.payout_account_name,
		})
		payoutSaved.value = true
		isEditing.value = false
		setTimeout(() => {
			payoutSaved.value = false
		}, 3000)
	} catch (err) {
		console.error('Failed to save payout info:', err)
	}
}

// Generate referral signup link
const referralLink = computed(() => {
	const code = stats.value.referral_code
	if (!code) return ''
	return `${window.location.origin}/login?ref=${code}`
})

// Copy referral link to clipboard
const copyReferralLink = async () => {
	const link = referralLink.value
	if (!link) return

	try {
		await navigator.clipboard.writeText(link)
		copied.value = true
		setTimeout(() => {
			copied.value = false
		}, 2000)
	} catch (err) {
		console.error('Failed to copy:', err)
	}
}

// Format currency in IDR
const formatCurrency = (amount) => {
	if (!amount) return 'Rp 0'
	return new Intl.NumberFormat('id-ID', {
		style: 'currency',
		currency: 'IDR',
		minimumFractionDigits: 0,
		maximumFractionDigits: 0,
	}).format(amount)
}
</script>


