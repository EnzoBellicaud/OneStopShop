<template>
    <footer>
        <div class="footer-inner">
            <div class="footer-logo">OneStop<span>Shop</span></div>
            <div class="footer-links">
            <a href="#">{{ t('footer.privacy') }}</a>
            <a href="#">{{ t('footer.terms') }}</a>
            <a href="#">{{ t('footer.universities') }}</a>
            <a href="#">{{ t('footer.contact') }}</a>
            </div>
            <div class="footer-copy">{{ t('footer.copyright', { year: currentYear }) }}</div>
        </div>
    </footer>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const currentYear = new Date().getFullYear()
</script>
