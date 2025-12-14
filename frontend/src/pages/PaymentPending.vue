<template>
	<div class="min-h-screen flex items-center justify-center bg-surface-gray-2">
		<div class="text-center bg-white rounded-lg shadow-lg p-8 max-w-md mx-4">
			<div class="mb-6">
				<div class="w-16 h-16 mx-auto bg-yellow-100 rounded-full flex items-center justify-center">
					<Clock class="w-8 h-8 text-yellow-600" />
				</div>
			</div>
			<h1 class="text-2xl font-bold text-ink-gray-9 mb-4">
				{{ __('Payment Pending') }}
			</h1>
			<p class="text-ink-gray-6 mb-6">
				{{ __('Your payment is being processed. Please complete the payment using your selected payment method.') }}
			</p>
			<p class="text-ink-gray-5 text-sm mb-6">
				{{ __('Once the payment is confirmed, you will be enrolled automatically. This may take a few minutes.') }}
			</p>
			<div class="space-y-3">
				<Button variant="solid" size="md" @click="goToCourses">
					{{ __('Go to Courses') }}
				</Button>
				<Button variant="outline" size="md" @click="checkStatus">
					{{ __('Check Payment Status') }}
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Button, usePageMeta } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { Clock } from 'lucide-vue-next'
import { sessionStore } from '../stores/session'

const router = useRouter()
const { brand } = sessionStore()

const goToCourses = () => {
	router.push({ name: 'Courses' })
}

const checkStatus = () => {
	// Reload the page to check if webhook has updated the status
	window.location.reload()
}

usePageMeta(() => {
	return {
		title: __('Payment Pending'),
		icon: brand.favicon,
	}
})
</script>
