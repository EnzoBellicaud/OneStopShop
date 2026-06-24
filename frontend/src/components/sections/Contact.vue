<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
    <section class="contact" id="contact">
        <div class="contact-inner">
            <div>
            <h2>{{ t('contact.titlePre') }} <em>{{ t('contact.titleEm') }}</em></h2>
            <p>{{ t('contact.desc') }}</p>
            </div>
            <div class="contact-form">
            <div class="form-row">
                <input class="form-input" type="text" :placeholder="t('contact.namePlaceholder')">
                <input class="form-input" type="email" :placeholder="t('contact.emailPlaceholder')">
            </div>
            <input class="form-input" type="text" :placeholder="t('contact.subjectPlaceholder')">
            <textarea class="form-textarea" :placeholder="t('contact.messagePlaceholder')"></textarea>
            <button class="btn-submit">{{ t('contact.send') }}</button>
            </div>
        </div>
    </section>
</template>
