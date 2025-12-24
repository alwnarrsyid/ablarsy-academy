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
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-lg font-semibold text-ink-gray-9">
					{{ __('Earnings Summary') }}
				</h2>
				<Button
					v-if="stats.pending_payout > 0 && hasPayoutMethod"
					variant="solid"
					@click="showWithdrawDialog = true"
				>
					<template #prefix>
						<Banknote class="w-4 h-4" />
					</template>
					{{ __('Request Withdrawal') }}
				</Button>
			</div>
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
			<!-- No payout method warning -->
			<div v-if="stats.pending_payout > 0 && !hasPayoutMethod" class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
				<p class="text-sm text-yellow-800">
					<AlertCircle class="w-4 h-4 inline-block mr-1" />
					{{ __('Please set up your payout method below before requesting a withdrawal.') }}
				</p>
			</div>
		</div>

		<!-- Withdraw Confirmation Dialog -->
		<Dialog v-model="showWithdrawDialog" :options="{ title: __('Request Withdrawal'), size: 'md' }">
			<template #body-content>
				<div class="space-y-4">
					<!-- Amount -->
					<div class="bg-surface-gray-2 rounded-lg p-4 text-center">
						<div class="text-sm text-ink-gray-5 mb-1">{{ __('Withdrawal Amount') }}</div>
						<div class="text-3xl font-bold text-ink-gray-9">
							{{ formatCurrency(stats.pending_payout) }}
						</div>
					</div>

					<!-- Payout Details -->
					<div class="border border-outline-gray-2 rounded-lg p-4 space-y-3">
						<div class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Payout Method') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ payoutForm.payout_method }}</span>
						</div>
						<div v-if="isEWallet" class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Phone Number') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ payoutForm.payout_phone }}</span>
						</div>
						<div v-if="isBankTransfer" class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Bank') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ payoutForm.payout_bank }}</span>
						</div>
						<div v-if="isBankTransfer" class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Account Number') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ payoutForm.payout_account_number }}</span>
						</div>
						<div v-if="isBankTransfer" class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Account Name') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ payoutForm.payout_account_name }}</span>
						</div>
					</div>

					<!-- User Info -->
					<div class="border border-outline-gray-2 rounded-lg p-4 space-y-3">
						<div class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Name') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ profile.data?.full_name }}</span>
						</div>
						<div class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Email') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ profile.data?.name }}</span>
						</div>
						<div class="flex justify-between text-sm">
							<span class="text-ink-gray-5">{{ __('Referral Code') }}</span>
							<span class="text-ink-gray-9 font-medium">{{ stats.referral_code }}</span>
						</div>
					</div>

					<!-- Note -->
					<div class="text-xs text-ink-gray-5 text-center">
						{{ __('Withdrawal requests are processed on the 25th of each month. Requests made after the 20th will be processed the following month.') }}
					</div>

					<!-- Error Message -->
					<div v-if="withdrawError" class="p-3 bg-red-50 border border-red-200 rounded-lg">
						<p class="text-sm text-red-700">{{ withdrawError }}</p>
					</div>

					<!-- Success Message -->
					<div v-if="withdrawSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg">
						<p class="text-sm text-green-700">
							<CheckCircle class="w-4 h-4 inline-block mr-1" />
							{{ __('Withdrawal request submitted successfully!') }}
						</p>
					</div>
				</div>
			</template>
			<template #actions>
				<Button variant="ghost" @click="showWithdrawDialog = false" :disabled="withdrawLoading">
					{{ __('Cancel') }}
				</Button>
				<Button
					variant="solid"
					@click="submitWithdrawRequest"
					:loading="withdrawLoading"
					:disabled="withdrawSuccess"
				>
					<template #prefix>
						<Send class="w-4 h-4" />
					</template>
					{{ __('Submit Request') }}
				</Button>
			</template>
		</Dialog>

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
import { createResource, Button, Badge, Dialog } from 'frappe-ui'
import { Copy, Wallet, Save, Smartphone, Library, Pencil, Banknote, AlertCircle, Send, CheckCircle } from 'lucide-vue-next'

const dayjs = inject('$dayjs')
const copied = ref(false)
const payoutSaved = ref(false)
const isEditing = ref(false)

// Withdraw dialog state
const showWithdrawDialog = ref(false)
const withdrawLoading = ref(false)
const withdrawError = ref('')
const withdrawSuccess = ref(false)

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

// Submit withdrawal request to webhook
const submitWithdrawRequest = async () => {
	withdrawLoading.value = true
	withdrawError.value = ''
	withdrawSuccess.value = false

	try {
		// Prepare withdrawal data
		const withdrawalData = {
			// User info
			user_email: props.profile.data?.name,
			user_name: props.profile.data?.full_name,
			user_id: props.profile.data?.name,

			// Referral info
			referral_code: stats.value.referral_code,
			total_referrals: stats.value.total_referrals || 0,
			total_earnings: stats.value.total_earnings || 0,

			// Withdrawal details
			withdrawal_amount: stats.value.pending_payout || 0,
			request_date: new Date().toISOString(),

			// Payout method - only send relevant fields
			payout_method: payoutForm.payout_method,
			// For E-Wallet (GoPay, Dana, OVO, ShopeePay) - send phone
			...(isEWallet.value && {
				payout_phone: payoutForm.payout_phone
			}),
			// For Bank Transfer - send bank details
			...(isBankTransfer.value && {
				payout_bank: payoutForm.payout_bank,
				payout_account_number: payoutForm.payout_account_number,
				payout_account_name: payoutForm.payout_account_name
			}),

			// Commission details (unpaid ones)
			pending_commissions: commissions.data
				?.filter(c => c.payout_status === 'Unpaid')
				?.map(c => ({
					id: c.name,
					student: c.referred_student,
					amount: c.commission_amount,
					date: c.creation
				})) || []
		}

		// Send to webhook
		const response = await fetch('https://n8n.srv799171.hstgr.cloud/webhook/wd-commision', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(withdrawalData)
		})

		if (!response.ok) {
			throw new Error('Failed to submit withdrawal request')
		}

		withdrawSuccess.value = true

		// Refresh data after 2 seconds and close dialog
		setTimeout(() => {
			showWithdrawDialog.value = false
			withdrawSuccess.value = false
			referralStats.reload()
			commissions.reload()
		}, 2000)

	} catch (err) {
		console.error('Withdrawal request failed:', err)
		withdrawError.value = err.message || 'Failed to submit withdrawal request. Please try again.'
	} finally {
		withdrawLoading.value = false
	}
}
</script>


