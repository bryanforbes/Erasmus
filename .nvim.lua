vim.opt.exrc = false

vim.lsp.config('basedpyright', {
	settings = {
		basedpyright = {
			disableOrganizeImports = true,
			analysis = {
				diagnosticMode = 'workspace',
			},
		},
	},
})
