<template>
	<div class="min-h-screen flex items-center justify-center bg-surface-gray-2">
		<div class="text-center bg-white rounded-lg shadow-lg p-8 max-w-md mx-4">
			<div class="mb-6">
				<div class="w-16 h-16 mx-auto bg-red-100 rounded-full flex items-center justify-center">
					<XCircle class="w-8 h-8 text-red-600" />
				</div>
			</div>
			<h1 class="text-2xl font-bold text-ink-gray-9 mb-4">
				{{ __('Payment Failed') }}
			</h1>
			<p class="text-ink-gray-6 mb-6">
				{{ __('We were unable to process your payment. This could be due to insufficient funds, card issues, or a timeout.') }}
			</p>
			<p class="text-ink-gray-5 text-sm mb-6">
				{{ __('Please try again or use a different payment method.') }}
			</p>
			<div class="space-y-3">
				<Button variant="solid" size="md" @click="goBack">
					{{ __('Try Again') }}
				</Button>
				<Button variant="outline" size="md" @click="goToCourses">
					{{ __('Go to Courses') }}
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Button, usePageMeta } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { XCircle } from 'lucide-vue-next'
import { sessionStore } from '../stores/session'

const router = useRouter()
const { brand } = sessionStore()

const goBack = () => {
	router.back()
}

const goToCourses = () => {
	router.push({ name: 'Courses' })
}

usePageMeta(() => {
	return {
		title: __('Payment Error'),
		icon: brand.favicon,
	}
})
</script>
