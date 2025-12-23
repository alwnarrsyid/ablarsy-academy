<template>
	<div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
		<div class="w-full max-w-md">
			<!-- Card -->
			<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
				<!-- Header -->
				<div class="text-center mb-8">
					<h1 class="text-xl font-semibold text-gray-900 mb-2">
						{{ __('Verify Your Email') }}
					</h1>
					<p class="text-sm text-gray-600">
						{{ __('We sent a 6-digit code to') }}
						<span class="font-medium text-gray-900">{{ email }}</span>
					</p>
				</div>

				<!-- Success State -->
				<div v-if="verified" class="text-center">
					<div
						class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4"
					>
						<CheckCircle class="w-8 h-8 text-green-600" />
					</div>
					<p class="text-gray-900 font-medium mb-2">
						{{ __('Email Verified!') }}
					</p>
					<p class="text-sm text-gray-600 mb-6">
						{{ __('Redirecting to set your password...') }}
					</p>
				</div>

				<!-- OTP Form -->
				<form v-else @submit.prevent="verifyOtp" class="space-y-6">
					<!-- OTP Input -->
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-2">
							{{ __('Verification Code') }}
						</label>
						<div class="flex gap-2 justify-center">
							<input
								v-for="(digit, index) in otpDigits"
								:key="index"
								:ref="(el) => (otpInputs[index] = el)"
								type="text"
								maxlength="1"
								v-model="otpDigits[index]"
								@input="handleInput(index, $event)"
								@keydown="handleKeydown(index, $event)"
								@paste="handlePaste"
								class="w-12 h-14 text-center text-xl font-semibold border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none transition-all"
								:class="{ 'border-red-500': error }"
							/>
						</div>
						<p v-if="error" class="mt-2 text-sm text-red-600 text-center">
							{{ error }}
						</p>
					</div>

					<!-- Submit Button -->
					<Button
						type="submit"
						variant="solid"
						class="w-full"
						:loading="loading"
						:disabled="!isOtpComplete"
					>
						{{ __('Verify Email') }}
					</Button>

					<!-- Resend OTP -->
					<div class="text-center">
						<p class="text-sm text-gray-600">
							{{ __("Didn't receive the code?") }}
							<button
								type="button"
								@click="resendOtp"
								:disabled="resendCountdown > 0"
								class="font-medium text-gray-900 hover:underline disabled:text-gray-400 disabled:no-underline"
							>
								<span v-if="resendCountdown > 0">
									{{ __('Resend in') }} {{ resendCountdown }}s
								</span>
								<span v-else>{{ __('Resend') }}</span>
							</button>
						</p>
					</div>
				</form>
			</div>

			<!-- Back to Login -->
			<div class="text-center mt-6">
				<a
					href="/login"
					class="text-sm text-gray-600 hover:text-gray-900"
				>
					← {{ __('Back to Login') }}
				</a>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Button, createResource } from 'frappe-ui'
import { CheckCircle } from 'lucide-vue-next'

const route = useRoute()

const email = ref('')
const otpDigits = ref(['', '', '', '', '', ''])
const otpInputs = ref([])
const loading = ref(false)
const error = ref('')
const verified = ref(false)
const resendCountdown = ref(60)
let countdownInterval = null

const isOtpComplete = computed(() => {
	return otpDigits.value.every((digit) => digit !== '')
})

const otpValue = computed(() => {
	return otpDigits.value.join('')
})

onMounted(() => {
	email.value = route.query.email || ''
	if (!email.value) {
		window.location.href = '/login'
		return
	}
	startResendCountdown()
	// Focus first input
	setTimeout(() => {
		if (otpInputs.value[0]) {
			otpInputs.value[0].focus()
		}
	}, 100)
})

onUnmounted(() => {
	if (countdownInterval) {
		clearInterval(countdownInterval)
	}
})

function startResendCountdown() {
	resendCountdown.value = 60
	if (countdownInterval) {
		clearInterval(countdownInterval)
	}
	countdownInterval = setInterval(() => {
		resendCountdown.value--
		if (resendCountdown.value <= 0) {
			clearInterval(countdownInterval)
		}
	}, 1000)
}

function handleInput(index, event) {
	const value = event.target.value

	// Only allow numbers
	if (!/^\d*$/.test(value)) {
		otpDigits.value[index] = ''
		return
	}

	error.value = ''

	// Move to next input
	if (value && index < 5) {
		otpInputs.value[index + 1]?.focus()
	}

	// Auto submit when complete
	if (isOtpComplete.value) {
		verifyOtp()
	}
}

function handleKeydown(index, event) {
	// Handle backspace
	if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
		otpInputs.value[index - 1]?.focus()
	}
}

function handlePaste(event) {
	event.preventDefault()
	const pastedData = event.clipboardData
		.getData('text')
		.replace(/\D/g, '')
		.slice(0, 6)

	for (let i = 0; i < pastedData.length; i++) {
		otpDigits.value[i] = pastedData[i]
	}

	// Focus last filled or next empty
	const focusIndex = Math.min(pastedData.length, 5)
	otpInputs.value[focusIndex]?.focus()

	if (isOtpComplete.value) {
		verifyOtp()
	}
}

const verifyOtpResource = createResource({
	url: 'lms.lms.api.verify_otp',
	makeParams() {
		return {
			email: email.value,
			otp: otpValue.value,
		}
	},
})

async function verifyOtp() {
	if (!isOtpComplete.value) return

	loading.value = true
	error.value = ''

	try {
		const response = await verifyOtpResource.submit()

		if (response.success) {
			verified.value = true
			// Redirect to update password page (Frappe route, not Vue)
			setTimeout(() => {
				window.location.href = '/update-password?key=' + response.reset_key
			}, 1500)
		} else {
			error.value = response.message || 'Invalid OTP'
			// Clear OTP inputs
			otpDigits.value = ['', '', '', '', '', '']
			otpInputs.value[0]?.focus()
		}
	} catch (err) {
		error.value = err.message || 'Verification failed'
		otpDigits.value = ['', '', '', '', '', '']
		otpInputs.value[0]?.focus()
	} finally {
		loading.value = false
	}
}

async function resendOtp() {
	if (resendCountdown.value > 0) return

	// Call n8n webhook to resend OTP
	try {
		await fetch('https://n8n.srv799171.hstgr.cloud/webhook/resend-otp', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email: email.value }),
		})
		startResendCountdown()
	} catch (err) {
		console.error('Failed to resend OTP:', err)
	}
}
</script>

<style scoped>
/* Hide number input spinners */
input[type='text']::-webkit-outer-spin-button,
input[type='text']::-webkit-inner-spin-button {
	-webkit-appearance: none;
	margin: 0;
}
</style>
